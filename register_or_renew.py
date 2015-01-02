# API PDR
# http://manage.publicdomainregistry.com/kb/answer/751
# http://manage.publicdomainregistry.com/kb/servlet/KBServlet/faq415.html
# Demo reseller ID: 568331;
# API key: ulHPQQ8uRCgUxpAkCeUbrkvY4O6qYByU;
# Customer ID: 11993326; test_customer@email.com:password9;
# Contact ID: 40859506;
# Test Order entity ID: 57909068; mlctest1.net;

# In registering/managing any domain name on the demo server always
# use ns1.onlyfordemo.net and ns2.onlyfordemo.net as your nameservers.
# ANY OTHER Nameserver will result in an INVALID NAMESERVER error.

import argparse
import requests


class BaseRegistrar(object):
    def __init__(self, name):
        self.name = name

    def call_api(self, domain, operation):
        return getattr(self, operation)(domain)

    def register(self, *a, **kw):
        raise NotImplementedError('subclasses must provide register() method')

    def renew(self, *a, **kw):
        raise NotImplementedError('subclasses must provide renew() method')


class PDR(BaseRegistrar):
    # Common static settings
    settings = {
            'auth-userid': '568331',
            'api-key': 'ulHPQQ8uRCgUxpAkCeUbrkvY4O6qYByU',
    }

    def register(self, domain):
        url = 'https://test.httpapi.com/api/domains/register.json'
        payload = {
            'domain-name': domain,
            'ns': ('ns1.onlyfordemo.net', 'ns2.onlyfordemo.net'),
            'years': '1',
            'customer-id': '11993326',
            'reg-contact-id': '40859506',
            'admin-contact-id': '40859506',
            'tech-contact-id': '40859506',
            'billing-contact-id': '40859506',
            'invoice-option': 'KeepInvoice',
        }
        payload.update(self.settings)

        r = requests.post(url, data=payload)
        status = r.json()['status']

        if status != 'Success':
            print r.json()
        return status

    def renew(self, domain):
        url = 'https://test.httpapi.com/api/domains/renew.json'
        payload = {
            'order-id': self.get_order_id(domain),
            'years': '1',
            'exp-date': '1', # Doesn't influence anything as long as not empty. Decided not to bother.
            'invoice-option': 'NoInvoice',
        }
        payload.update(self.settings)

        r = requests.post(url, data=payload)
        status = r.json()['status']

        if status != 'Success':
            print r.json()
        return status

    def get_order_id(self, domain):
        url = 'https://test.httpapi.com/api/domains/orderid.json'
        payload = {'domain-name': domain}
        payload.update(self.settings)

        r = requests.get(url, params=payload)

        if r.status_code == 200:
            return int(r.text)


class GoodMock(BaseRegistrar):
    def register(self, domain):
        return 'Success'

    def renew(self, domain):
        return 'Success'


class BadMock(BaseRegistrar):
    def register(self, domain):
        return 'Fail'

    def renew(self, domain):
        return 'Fail'


# Preformed dict with required order of registrars.
# GOOD_MOCK and BAD_MOCK always return success/fail respectively.
ZONES = {
    'com': ['PDR', 'GOOD_MOCK', 'BAD_MOCK'],
    'org': ['GOOD_MOCK', 'PDR', 'BAD_MOCK'],
    'net': ['BAD_MOCK', 'PDR', 'GOOD_MOCK'],
    'co.uk': ['BAD_MOCK', 'UNKNOWN_MOCK', 'PDR'],
}

REGISTRATORS = {
    'GOOD_MOCK': GoodMock('GOOD_MOCK'),
    'BAD_MOCK': BadMock('BAD_MOCK'),
    'PDR': PDR('PDR'),
}


def main():
    parser = argparse.ArgumentParser(description='Call multiple registrars APIs with a given domain')
    parser.add_argument("domain", help="Domain name, e.g.: 'foodom.com'")
    parser.add_argument("operation", choices=('register', 'renew'), help="Possible operations with domain")
    args = parser.parse_args()

    operation = args.operation
    domain = args.domain
    # Split zone from domain as 'foo.com' -> 'com', 'foo.co.uk' -> 'co.uk'
    zone = domain.split('.', 1)[1]

    reg_names = ZONES[zone] # Let it fail, KeyError here is self-explanatory

    for reg_name in reg_names:
        reg = REGISTRATORS.get(reg_name)
        try:
            result = reg.call_api(domain, operation)

            if result == 'Success':
                print "Registrar {0} - SUCCESS! Job finished.".format(reg_name)
                return
            else:
                print "Registrar {0} - failed. Trying next one in queue..".format(reg_name)
        except AttributeError:
            print "Warning: Unknown registrar {0} found in zone {1}. Please check settings".format(reg_name, zone)
        except:
            raise
    print "FAILED for all registrars. Job finished."


if __name__ == "__main__":
    main()
