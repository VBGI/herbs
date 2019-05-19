# coding: utf-8
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template import Context, Template
from django.core.urlresolvers import reverse


try:
    from herbs.models import Notification, HerbItem
except ImportError:
    from bgi.herbs.models import Notification, HerbItem

class Command(BaseCommand):
    args = ''
    help = 'Send notification messages'

    def handle(self, *args, **options):
        query = '''
        SELECT DISTINCT herbs_notification.hitem_id
        FROM herbs_notification INNER JOIN herbs_herbitem
        ON herbs_notification.hitem_id = herbs_herbitem.id
        WHERE herbs_notification.status='Q'
        ORDER BY herbs_notification.created DESC;
        '''
        cursor = connection.cursor()
        cursor.execute(query)

        messages = dict()
        for obj_id in [item[0] for item in cursor.fetchall()]:
            for item in Notification.objects.filter(hitem__id=obj_id, status='Q'):
                if item.emails:
                    for email in item.emails.split(','):
                        messages.setdefault(email, list()).append({
                            'id': obj_id,
                            'date': str(item.created),
                            'username': item.username,
                            'link': 'http://botsad.ru' + reverse('admin:%s_%s_change' % ('herbs', 'herbitem'),
                              args=[obj_id])
                            })
                        reason = u'<{}> : <{}>'.format(HerbItem._meta.get_field(item.tracked_field.split('_')[0]).verbose_name.decode('utf-8'), item.field_value)
                        if 'reason' not in messages[email][-1]:
                            messages[email][-1].update({'reason': [reason]})
                        else:
                            messages[email][-1]['reason'].append(reason)

                        if 'note_ids' not in messages[email][-1]:
                            messages[email][-1].update({'note_ids': [item.id]})
                        else:
                            messages[email][-1]['note_ids'].append(item.id)
        for email in messages:
            html = self._generate_html_message(messages[email])
            try:
                mail_msg = EmailMultiAlternatives(u'Оповещение гербария от %s' % timezone.now(),
                                        '', 'herbarium@botsad.ru',
                                        [email], connection=get_connection(fail_silently=False))
                mail_msg.attach_alternative(html, 'text/html')
                mail_msg.send()
                ids = sum([x['note_ids'] for x in messages[email]], [])
                Notification.objects.filter(id__in=ids).update(status='S')
            except:
                pass

    @staticmethod
    def _generate_html_message(msg):
        html_email_temaple = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
          <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
          <title>Demystifying Email Design</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        </head>
        <body style="margin: 0; padding: 0;">
         <table align="center" border="1" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse;">
          <tr>
           <td bgcolor="#e2f4f3" style="padding: 10px 10px 10px 10px;">
            <h2 style="text-align:center"> Сводка по изменениям в гербарии от {{created}} </h2>
           </td>
          </tr>
          <tr>
              <td bgcolor="#ffffff" style="padding: 40px 40px 40px 40px;">
                 <table border="1" cellpadding="0" cellspacing="0" width="100%">
                  <tr style="background-color: #daedbb">
                   <td align="center">ID</td>
                   <td align="center">USERNAME</td>
                   <td align="center">DATE</td>
                   <td align="center">REASON<br> &lt;FIELD&gt;:&lt;VALUE&gt;</td>
                   <td align="center">EDIT<br>LINK</td>
                  </tr>
                  {%for item in items %}
                    {% if forloop.counter|divisibleby:2 %}
                        <tr style="background-color: #d9e5ef">
                           <td align="center">{{item.id}}</td>
                           <td align="center">{{item.username}}</td>
                           <td align="center">{{item.date}}</td>
                           <td align="center">{%for field in item.reason %}<p>{{field}}</p>{%endfor%}</td>
                           <td align="center"><a href="{{item.link|safe}}">Edit</a></td>
                        </tr>
                    {%else%}
                        <tr style="background-color: #d7dce1">
                           <td align="center">{{item.id}}</td>
                           <td align="center">{{item.username}}</td>
                           <td align="center">{{item.date}}</td>
                           <td align="center">{%for field in item.reason %}<p>{{field}}</p>{%endfor%}</td>
                           <td align="center"><a href="{{item.link|safe}}">Edit</a></td>
                        </tr>
                    {%endif%}
                  {%endfor%}
                 </table>
              </td>
          </tr>
         </table>
        </body>
        </html>
        """
        template = Template(html_email_temaple)
        context = Context({'items': msg, 'created': timezone.now()})
        return template.render(context)














