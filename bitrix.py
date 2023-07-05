from fast_bitrix24 import Bitrix


def send_data_to_bitrix24(user_data):
    webhook = 'https://portal.ekoservis.ru/rest/1/4wfefwu80r1trc3q/'
    b = Bitrix(webhook)
    BITRIX24_LEAD_FIELD_MAPPING = {'fields': {
            'NAME': user_data['name'],
            'PHONE': user_data['phone'],
            'COMPANY_TITLE': user_data['inn'],
            'ADDRESS': user_data['location'],
            'COMMENTS': user_data['volume'] + '\n' + user_data['waste_type'] + '\n' + user_data['loading'] +
                        '\n' + user_data['transport_restrictions'],
            'SOURCE_DESCRIPTION': user_data['urgency']
        }}
    b.call('crm.lead.add', BITRIX24_LEAD_FIELD_MAPPING)
