import logging
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.core.mail import EmailMultiAlternatives
from django.core.mail import get_connection
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import permalink
from django.template import Context
from django.template.loader import select_template
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.timezone import now
import sorl.thumbnail
from sorl.thumbnail import ImageField
from .utils import (
    make_activation_code, get_default_sites, ACTIONS
)

logger = logging.getLogger(__name__)

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


@python_2_unicode_compatible
class Newsletter(models.Model):
    site = models.ManyToManyField(Site, default=get_default_sites)

    title = models.CharField(
        max_length=200, verbose_name=_('Título del newsletter')
    )
    slug = models.SlugField(db_index=True, unique=True)

    email = models.EmailField(
        verbose_name=_('e-mail'), help_text=_('E-mail de envio')
    )
    sender = models.CharField(
        max_length=200, verbose_name=_('Remitente'), help_text=_('Nombre del remitente')
    )

    visible = models.BooleanField(
        default=True, verbose_name=_('visible'), db_index=True
    )

    send_html = models.BooleanField(
        default=True, verbose_name=_('Enviar html?'),
        help_text=_('Enviar el mensaje como HTML?')
    )

    objects = models.Manager()

    # Automatically filter the current site
    on_site = CurrentSiteManager()

    def get_templates(self, action):
        """
        Return a subject, text, HTML tuple with e-mail templates for
        a particular action. Returns a tuple with subject, text and e-mail
        template.
        """

        assert action in ACTIONS + ('message',), 'Unknown action: %s' % action

        # Common substitutions for filenames
        tpl_subst = {
            'action': action,
            'newsletter': self.slug
        }

        # Common root path for all the templates
        tpl_root = 'newsletter/message/'

        subject_template = select_template([
            tpl_root + '%(newsletter)s/%(action)s_subject.txt' % tpl_subst,
            tpl_root + '%(action)s_subject.txt' % tpl_subst,
        ])

        text_template = select_template([
            tpl_root + '%(newsletter)s/%(action)s.txt' % tpl_subst,
            tpl_root + '%(action)s.txt' % tpl_subst,
        ])

        if self.send_html:
            html_template = select_template([
                tpl_root + '%(newsletter)s/%(action)s.html' % tpl_subst,
                tpl_root + '%(action)s.html' % tpl_subst,
            ])
        else:
            # HTML templates are not required
            html_template = None

        return (subject_template, text_template, html_template)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('newsletter')
        verbose_name_plural = _('newsletters')

    @permalink
    def get_absolute_url(self):
        return (
            'newsletter_detail', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def subscribe_url(self):
        return (
            'newsletter_subscribe_request', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def unsubscribe_url(self):
        return (
            'newsletter_unsubscribe_request', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def update_url(self):
        return (
            'newsletter_update_request', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def archive_url(self):
        return (
            'newsletter_archive', (),
            {'newsletter_slug': self.slug}
        )

    def get_sender(self):
        return u'%s <%s>' % (self.sender, self.email)

    def get_subscriptions(self):
        logger.debug(u'Looking up subscribers for %s', self)

        return Subscription.objects.filter(newsletter=self, subscribed=True)

    @classmethod
    def get_default(cls):
        try:
            return cls.objects.all()[0]
        except IndexError:
            return None


@python_2_unicode_compatible
class Subscription(models.Model):
    user = models.ForeignKey(
        AUTH_USER_MODEL, blank=True, null=True, verbose_name=_('user')
    )

    name_field = models.CharField(
        db_column='name', max_length=30, blank=True, null=True,
        verbose_name=_('name'), help_text=_('optional')
    )

    def get_name(self):
        if self.user:
            return self.user.get_full_name()
        return self.name_field

    def set_name(self, name):
        if not self.user:
            self.name_field = name

    name = property(get_name, set_name)

    email_field = models.EmailField(
        db_column='email', verbose_name=_('e-mail'), db_index=True,
        blank=True, null=True
    )

    def get_email(self):
        if self.user:
            return self.user.email
        return self.email_field

    def set_email(self, email):
        if not self.user:
            self.email_field = email

    email = property(get_email, set_email)

    def update(self, action):
        """
        Update subscription according to requested action:
        subscribe/unsubscribe/update/, then save the changes.
        """

        assert action in ('subscribe', 'update', 'unsubscribe')

        # If a new subscription or update, make sure it is subscribed
        # Else, unsubscribe
        if action == 'subscribe' or action == 'update':
            self.subscribed = True
        else:
            self.unsubscribed = True

        logger.debug(
            _(u'Updated subscription %(subscription)s to %(action)s.'),
            {
                'subscription': self,
                'action': action
            }
        )

        # This triggers the subscribe() and/or unsubscribe() methods, taking
        # care of stuff like maintaining the (un)subscribe date.
        self.save()

    def _subscribe(self):
        """
        Internal helper method for managing subscription state
        during subscription.
        """
        logger.debug(u'Subscribing subscription %s.', self)

        self.subscribe_date = now()
        self.subscribed = True
        self.unsubscribed = False

    def _unsubscribe(self):
        """
        Internal helper method for managing subscription state
        during unsubscription.
        """
        logger.debug(u'Unsubscribing subscription %s.', self)

        self.subscribed = False
        self.unsubscribed = True
        self.unsubscribe_date = now()

    def save(self, *args, **kwargs):
        """
        Perform some basic validation and state maintenance of Subscription.

        TODO: Move this code to a more suitable place (i.e. `clean()`) and
        cleanup the code. Refer to comment below and
        https://docs.djangoproject.com/en/dev/ref/models/instances/#django.db.models.Model.clean
        """
        assert self.user or self.email_field, \
            _('Neither an email nor a username is set. This asks for '
              'inconsistency!')
        assert ((self.user and not self.email_field) or
                (self.email_field and not self.user)), \
            _('If user is set, email must be null and vice versa.')

        # This is a lame way to find out if we have changed but using Django
        # API internals is bad practice. This is necessary to discriminate
        # from a state where we have never been subscribed but is mostly for
        # backward compatibility. It might be very useful to make this just
        # one attribute 'subscribe' later. In this case unsubscribed can be
        # replaced by a method property.

        if self.pk:
            assert (Subscription.objects.filter(pk=self.pk).count() == 1)

            subscription = Subscription.objects.get(pk=self.pk)
            old_subscribed = subscription.subscribed
            old_unsubscribed = subscription.unsubscribed

            # If we are subscribed now and we used not to be so, subscribe.
            # If we user to be unsubscribed but are not so anymore, subscribe.
            if ((self.subscribed and not old_subscribed) or
                    (old_unsubscribed and not self.unsubscribed)):
                self._subscribe()

                assert not self.unsubscribed
                assert self.subscribed

            # If we are unsubcribed now and we used not to be so, unsubscribe.
            # If we used to be subscribed but are not subscribed anymore,
            # unsubscribe.
            elif ((self.unsubscribed and not old_unsubscribed) or
                      (old_subscribed and not self.subscribed)):
                self._unsubscribe()

                assert not self.subscribed
                assert self.unsubscribed
        else:
            if self.subscribed:
                self._subscribe()
            elif self.unsubscribed:
                self._unsubscribe()

        super(Subscription, self).save(*args, **kwargs)

    # ip = models.GenericIPAddressField(_("IP address"), blank=True, null=True)

    newsletter = models.ForeignKey('Newsletter', verbose_name=_('newsletter'))

    create_date = models.DateTimeField(editable=False, auto_now_add=True)

    activation_code = models.CharField(
        verbose_name=_('activation code'), max_length=40,
        default=make_activation_code
    )

    subscribed = models.BooleanField(
        default=False, verbose_name=_('suscrito'), db_index=True
    )
    subscribe_date = models.DateTimeField(
        verbose_name=_("fecha de suscripción"), null=True, blank=True
    )

    # This should be a pseudo-field, I reckon.
    unsubscribed = models.BooleanField(
        default=False, verbose_name=_('no suscrito'), db_index=True
    )
    unsubscribe_date = models.DateTimeField(
        verbose_name=_("unsubscribe date"), null=True, blank=True
    )

    def __str__(self):
        if self.name:
            return _(u"%(name)s <%(email)s> to %(newsletter)s") % {
                'name': self.name,
                'email': self.email,
                'newsletter': self.newsletter
            }

        else:
            return _(u"%(email)s to %(newsletter)s") % {
                'email': self.email,
                'newsletter': self.newsletter
            }

    class Meta:
        verbose_name = _('suscripción')
        verbose_name_plural = _('suscripciones')
        unique_together = ('user', 'email_field', 'newsletter')

    def get_recipient(self):
        if self.name:
            return u'%s <%s>' % (self.name, self.email)

        return u'%s' % (self.email)

    def send_activation_email(self, action):
        assert action in ACTIONS, 'Unknown action: %s' % action

        (subject_template, text_template, html_template) = \
            self.newsletter.get_templates(action)

        variable_dict = {
            'subscription': self,
            'site': Site.objects.get_current(),
            'newsletter': self.newsletter,
            'date': self.subscribe_date,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL
        }

        unescaped_context = Context(variable_dict, autoescape=False)

        subject = subject_template.render(unescaped_context).strip()
        text = text_template.render(unescaped_context)

        message = EmailMultiAlternatives(
            subject, text,
            from_email=self.newsletter.get_sender(),
            to=[self.email]
        )

        if html_template:
            escaped_context = Context(variable_dict)

            message.attach_alternative(
                html_template.render(escaped_context), "text/html"
            )

        message.send()

        logger.debug(
            u'Activation email sent for action "%(action)s" to %(subscriber)s '
            u'with activation code "%(action_code)s".', {
                'action_code': self.activation_code,
                'action': action,
                'subscriber': self
            }
        )

    @permalink
    def subscribe_activate_url(self):
        return ('newsletter_update_activate', (), {
            'newsletter_slug': self.newsletter.slug,
            'email': self.email,
            'action': 'subscribe',
            'activation_code': self.activation_code
        })

    @permalink
    def unsubscribe_activate_url(self):
        return ('newsletter_update_activate', (), {
            'newsletter_slug': self.newsletter.slug,
            'email': self.email,
            'action': 'unsubscribe',
            'activation_code': self.activation_code
        })

    @permalink
    def update_activate_url(self):
        return ('newsletter_update_activate', (), {
            'newsletter_slug': self.newsletter.slug,
            'email': self.email,
            'action': 'update',
            'activation_code': self.activation_code
        })


@python_2_unicode_compatible
class Article(models.Model):
    """
    An Article within a Message which will be send through a Submission.
    """

    @classmethod
    def get_next_order(cls):
        """
        Get the next available Article ordering as to assure uniqueness.
        """

        next_order = cls.objects.aggregate(
            models.Max('sortorder')
        )['sortorder__max']

        if next_order:
            return next_order + 10
        else:
            return 10

    sortorder = models.PositiveIntegerField(
        help_text=_('Indica la posición del artículo dentro del post'),
        verbose_name=_('Orden'), db_index=True,
    )

    title = models.CharField(max_length=200, verbose_name=_('título'))
    text = models.TextField(verbose_name=_('texto'))

    url = models.URLField(
        verbose_name=_('link'), default='http://www.buenviajeacuba.com'
    )

    # Make this a foreign key for added elegance
    image = ImageField(
        upload_to='newsletter/images/%Y/%m/%d', verbose_name=_('image')
    )

    # Message this article is associated with
    # TODO: Refactor post to message (post is legacy notation).
    post = models.ForeignKey(
        'Message', verbose_name=_('message'), related_name='articles'
    )

    class Meta:
        ordering = ('sortorder',)
        verbose_name = _('artículo')
        verbose_name_plural = _('artículos')

    def __str__(self):
        return self.title

    def get_width_top(self):
        new_image = sorl.thumbnail.get_thumbnail(self.image, '142x100')
        return new_image, new_image.width, new_image.height

    def save(self):
        if self.pk is None:
            # If saving a new object get the next available Article ordering
            # as to assure uniqueness.
            self.sortorder = Article.get_next_order()
        self.text = self.text.split('>', 1)[1].rsplit('<', 1)[0]
        super(Article, self).save()


@python_2_unicode_compatible
class Publicity(models.Model):
    """
    An publicity within a Message which will be send through a Submission.
    """

    @classmethod
    def get_next_order(cls):
        """
        Get the next available Publicity ordering as to assure uniqueness.
        """

        next_order = cls.objects.aggregate(
            models.Max('sortorder')
        )['sortorder__max']

        if next_order:
            return next_order + 10
        else:
            return 10

    sortorder = models.PositiveIntegerField(
        help_text=_('Indica la posición de la publicidad dentro del newsletter'),
        verbose_name=_('Orden'), db_index=True,
        # default=lambda: Publicity.get_next_order()
    )

    title = models.CharField(max_length=200, verbose_name=_('title'))
    url = models.URLField(
        verbose_name=_('link')
    )

    # Make this a foreign key for added elegance
    image = ImageField(
        upload_to='newsletter/images/%Y/%m/%d',
        verbose_name=_('image')
    )

    # Message this article is associated with
    post = models.ForeignKey(
        'Message', verbose_name=_('message'), related_name='publicities'
    )

    class Meta:
        ordering = ('sortorder',)
        verbose_name = _('publicidad')
        verbose_name_plural = _('publicidades')

    def __str__(self):
        return self.title

    def get_width_top(self, width, height):
        sizes = width.__str__() + 'x' + height.__str__()
        # print(sizes)
        new_image = sorl.thumbnail.get_thumbnail(self.image, sizes)
        return (new_image, (width - new_image.width) / 2, (height - new_image.height) / 2, self.url)

    def save(self):
        if self.pk is None:
            # If saving a new object get the next available Article ordering
            # as to assure uniqueness.
            self.sortorder = Article.get_next_order()
        super(Publicity, self).save()


@python_2_unicode_compatible
class Message(models.Model):
    """ Message as sent through a Submission. """

    title = models.CharField(max_length=200, verbose_name=_('title'))
    slug = models.SlugField(verbose_name=_('slug'))
    image = ImageField(
        upload_to='newsletter/images/%Y/%m/%d', blank=True, null=True,
        verbose_name=_('imagen')
    )

    newsletter = models.ForeignKey(
        'Newsletter', verbose_name=_('newsletter')
    )

    date_create = models.DateTimeField(
        verbose_name=_('created'), auto_now_add=True, editable=False
    )
    date_modify = models.DateTimeField(
        verbose_name=_('modified'), auto_now=True, editable=False
    )

    def __str__(self):
        try:
            return _(u"%(title)s in %(newsletter)s") % {
                'title': self.title,
                'newsletter': self.newsletter
            }
        except Newsletter.DoesNotExist:
            logger.warn(
                'Database inconsistency, related newsletter not found '
                'for message with id %d', self.id
            )

            return "%s" % self.title

    class Meta:
        verbose_name = _('mensaje')
        verbose_name_plural = _('mensajes')
        unique_together = ('slug', 'newsletter')

    def save(self, **kwargs):
        if self.pk is None:
            self.newsletter = Newsletter.get_default()
        super(Message, self).save(**kwargs)

    @classmethod
    def get_default(cls):
        try:
            return cls.objects.order_by('-date_create').all()[0]
        except IndexError:
            return None


@python_2_unicode_compatible
class Submission(models.Model):
    """
    Submission represents a particular Message as it is being submitted
    to a list of Subscribers. This is where actual queueing and submission
    happends.
    """

    class Meta:
        verbose_name = _('envio')
        verbose_name_plural = _('envios')

    def __str__(self):
        return _(u"%(newsletter)s on %(publish_date)s") % {
            'newsletter': self.message,
            'publish_date': self.publish_date
        }

    def submit(self):
        subscriptions = self.subscriptions.filter(subscribed=True)

        logger.info(
            ugettext(u"Enviando %(submission)s a %(count)d suscriptores"),
            {'submission': self, 'count': subscriptions.count()}
        )

        assert self.publish_date < now(), \
            'Something smells fishy; submission time in future.'

        self.sending = True
        self.save()

        try:
            (subject_template, text_template, html_template) = \
                self.message.newsletter.get_templates('message')

            try:
                connection = get_connection()
                connection.open()

                self.sending = True
                self.save()

                simple = False
                if self.message.publicities.all().__len__() < 7:
                    simple = True

                news_pict = False

                try:
                    new_image = sorl.thumbnail.get_thumbnail(self.message.image, '470x150')
                    news_pict = new_image
                except:
                    news_pict = False

                same_variable_dict = {
                    'site': Site.objects.get_current(),
                    'issue': self.message.get_default(),
                    'submission': self,
                    'message': self.message,
                    'newsletter': self.newsletter,
                    'date': self.publish_date,
                    'simple': simple,
                    'newspict': news_pict,
                    'STATIC_URL': settings.STATIC_URL,
                    'MEDIA_URL': settings.MEDIA_URL,
                    'sitio': settings.WEB_PAGE_URL
                }

                unescaped_context = Context(same_variable_dict, autoescape=False)

                subject = subject_template.render(unescaped_context).strip()
                text = text_template.render(unescaped_context)

                escaped_context = Context(same_variable_dict)

                html_message = html_template.render(escaped_context)

                for subscription in subscriptions:
                    variable_dict = {
                        'subscription': subscription
                    }
                    variable_dict.update(same_variable_dict)

                    message = EmailMultiAlternatives(
                        subject, text,
                        from_email=self.newsletter.get_sender(),
                        to=[subscription.get_recipient()], connection=connection
                    )

                    if html_template:
                        message.attach_alternative(
                            html_message,
                            "text/html"
                        )

                    try:
                        logger.debug(
                            ugettext(u'Submitting message to: %s.'),
                            subscription
                        )
                        # print('correo enviado')
                        message.send()
                        print('correo enviado a ' + subscription.get_recipient())

                    except Exception as e:
                        logger.error(
                            ugettext(u'Message %(subscription)s failed '
                                     u'with error: %(error)s'),
                            {'subscription': subscription,
                             'error': e}
                        )

                connection.close()
                self.sent = True
                return 'Mensajes enviados con éxito', 1

            except Exception as e:
                logger.error(
                    ugettext(u'There was a problem with the connection'
                             u'the error is: %(error)s'),
                    {'error': e}
                )
                self.sending = False
                self.sent = False
                self.prepared = False
                self.save()
                print(e)
                return 'Ocurrieron errores a la hora de enviar los mensajes', 0

        finally:
            self.sending = False
            self.save()

    @classmethod
    def submit_queue(cls):
        todo = cls.objects.filter(
            prepared=True, sent=False, sending=False,
            publish_date__lt=now()
        )

        for submission in todo:
            submission.submit()

    @classmethod
    def from_message(cls, message):
        logger.debug(ugettext('Submission of message %s'), message)
        submission = cls()
        submission.message = message
        submission.newsletter = message.newsletter
        submission.save()
        submission.subscriptions = message.newsletter.get_subscriptions()
        return submission

    def save(self):
        """ Set the newsletter from associated message upon saving. """
        assert self.message.newsletter

        self.newsletter = self.message.newsletter

        return super(Submission, self).save()

    @permalink
    def get_absolute_url(self):
        assert self.newsletter.slug
        assert self.message.slug

        return (
            'newsletter_archive_detail', (), {
                'newsletter_slug': self.newsletter.slug,
                'year': self.publish_date.year,
                'month': self.publish_date.month,
                'day': self.publish_date.day,
                'slug': self.message.slug
            }
        )

    newsletter = models.ForeignKey(
        'Newsletter', verbose_name=_('newsletter'), editable=False
    )
    message = models.ForeignKey(
        'Message', verbose_name=_('mensaje'), editable=True, null=False
    )

    subscriptions = models.ManyToManyField(
        'Subscription',
        help_text=_('If you select none, the system will automatically find '
                    'the subscribers for you.'),
        blank=True, db_index=True, verbose_name=_('suscriptores'),
        limit_choices_to={'subscribed': True}
    )

    publish_date = models.DateTimeField(
        verbose_name=_('fecha de envio'), blank=True, null=True,
        default=now, db_index=True
    )
    publish = models.BooleanField(
        default=True, verbose_name=_('publish'),
        help_text=_('Publish in archive.'), db_index=True
    )

    prepared = models.BooleanField(
        default=False, verbose_name=_('preparado'),
        db_index=True, editable=False
    )
    sent = models.BooleanField(
        default=False, verbose_name=_('enviado'),
        db_index=True, editable=False
    )
    sending = models.BooleanField(
        default=False, verbose_name=_('en proceso'),
        db_index=True, editable=False
    )
