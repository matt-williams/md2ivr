import requests
import datetime

URL_PREFIX = 'https://pbx.sipcentric.com/api/v1'

class SimwoodClient:
    def __init__(self, auth, customer_id=None):
        self.auth = auth
        self.get_me()
        self.customer_id = self.find_customer_id(customer_id)

    def get_me(self):
        r = requests.get('{}/users/me/'.format(URL_PREFIX), auth=self.auth)
        r.raise_for_status()
        self.print_ratelimit(r)
        return r.json()

    def print_ratelimit(self, r):
        print("{}/{} ({:.2f}%) requests remaining - reset in {} seconds".format(r.headers['X-RateLimit-Remaining'], r.headers['X-RateLimit-Limit'], int(r.headers['X-RateLimit-Remaining']) * 100. / int(r.headers['X-RateLimit-Limit']), datetime.timedelta(seconds=int(r.headers['X-RateLimit-Reset']))))

    def get_list(self, url):
        page = 1
        items = []
        while True:
            r = requests.get('{}?pageSize=200&page={}'.format(url, page), auth=self.auth)
            r.raise_for_status()
            data = r.json()
            if 'items' in data:
                items.extend(data['items'])
            if not 'nextPage' in data:
                break
            page += 1
        return items

    def find_customer_id(self, customer_id=None):
        customers = self.get_list('{}/customers'.format(URL_PREFIX))
        if not customer_id and len(customers) > 0:
            customer_id = customers[0]['id']
        for customer in customers:
            if customer['id'] == customer_id:
                print("Customer {}: {} {} ({})".format(customer_id, customer['firstName'], customer['lastName'], customer['company']))
                return customer_id
        else:
            if customer_id:
                raise IndexError('Customer {} not found'.format(customer_id))
            else:
                raise IndexError('No customer found!')

    def get_numbers(self):
        return self.get_list('{}/customers/{}/phonenumbers'.format(URL_PREFIX, self.customer_id))

    def get_number(self, number):
        for entry in self.get_numbers():
            if entry['number'] == number:
                return entry
        return None

    def update_destination(self, number, endpoint_id):
        number['destination'] = '{}/customers/{}/endpoints/{}'.format(URL_PREFIX, self.customer_id, endpoint_id)
        number['routingRules'] = []
        r = requests.put(number['uri'], json=number, auth=self.auth)
        r.raise_for_status()

    def get_endpoints(self):
        return self.get_list('{}/customers/{}/endpoints'.format(URL_PREFIX, self.customer_id))

    def get_ivr_endpoints(self):
        return [endpoint for endpoint in self.get_endpoints() if endpoint['type'] == 'ivr']

    def create_ivr_endpoint(self, short_number, name, prompt_id, actions=[], timeout=5, timeout_action=None, invalid_action=None):
        obj = {
            "type": "ivr",
            "shortNumber": short_number,
            "name": name,
            "entrySound": '{}/customers/{}/sounds/{}'.format(URL_PREFIX, self.customer_id, prompt_id),
            "items": actions,
            "timeout": timeout
        }
        if timeout_action:
            obj['timeoutAction'] = timeout_action
        if invalid_action:
            obj['timeoutAction'] = invalid_action
        r = requests.post('{}/customers/{}/endpoints'.format(URL_PREFIX, self.customer_id), json=obj, auth=self.auth)
        r.raise_for_status()
        endpoint_id = r.json()['id']
        return endpoint_id

    def update_endpoint_actions(self, endpoint, actions):
        endpoint['items'] = actions
        r = requests.put(endpoint['uri'], json=endpoint, auth=self.auth)
        r.raise_for_status()

    def delete_endpoint(self, endpoint_id):
        r = requests.delete('{}/customers/{}/endpoints/{}'.format(URL_PREFIX, self.customer_id, endpoint_id), auth=self.auth)
        r.raise_for_status()

    def get_endpoint_url(self, endpoint_id):
        return '{}/customers/{}/endpoints/{}'.format(URL_PREFIX, self.customer_id, endpoint_id)

    def get_sounds(self):
        return self.get_list('{}/customers/{}/sounds'.format(URL_PREFIX, self.customer_id))

    def get_prompts(self):
        return [sound for sound in self.get_sounds() if sound['type'] == 'prompt']

    def create_prompt(self, name, audio):
        return self.create_sound('prompt', name, audio)

    def create_sound(self, typ, name, audio):
        r = requests.post('{}/customers/{}/sounds'.format(URL_PREFIX, self.customer_id), json={"type": typ, "name": name}, auth=self.auth)
        r.raise_for_status()
        sound_id = r.json()['id']
        r = requests.put('{}/customers/{}/sounds/{}'.format(URL_PREFIX, self.customer_id, sound_id), headers={"Content-Type": "audio/wav"}, data=audio, auth=self.auth)
        r.raise_for_status()
        return sound_id

    def delete_sound(self, sound_id):
        r = requests.delete('{}/customers/{}/sounds/{}'.format(URL_PREFIX, self.customer_id, sound_id), auth=self.auth)
        r.raise_for_status()

if __name__ == "__main__":
    auth = ('xxx', 'xxx')
    client = SimwoodClient(auth)

    prompts = client.get_prompts()
    print(prompts)
    for prompt in prompts:
        if prompt['name'] == 'test':
            client.delete_sound(prompt['id'])
    import tts
    audio = tts.text_to_speech("This is a test")
    prompt_id = client.create_prompt("test", audio)
    print(prompt_id)

    endpoints = client.get_endpoints()
    print(endpoints)
    for endpoint in endpoints:
        if endpoint['name'] == 'test':
            client.delete_endpoint(endpoint['id'])
    endpoint_id = client.create_ivr_endpoint('{:03d}'.format(27), 'test', prompt_id)

    number = client.get_number("02081253476")
    print(number)
    client.update_destination(number, endpoint_id)

