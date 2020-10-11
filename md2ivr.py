#!/usr/local/bin/python3

import argparse
parser = argparse.ArgumentParser(description='Convert Markdown text (from STDIN) into a Simwood IVR menu')
parser.add_argument('number', type=str, help='Simwood number to apply the IVR to')
parser.add_argument('--user', type=str, required=True, help='Simwood username')
parser.add_argument('--password', type=str, required=True, help='Simwood password')
parser.add_argument('--prefix', type=str, default='', help='Simwood object name prefix')
parser.add_argument('--shortcode', type=str, default=1, help='Initial Simwood short code')
args = parser.parse_args()

import sys
text = sys.stdin.read()

import markdown
renderer = markdown.TextRenderer()
blocks = markdown.get_blocks(text)

from simwood import SimwoodClient
client = SimwoodClient((args.user, args.password))
number = client.get_number(args.number)
if not number:
    print("Number {} not found in account".format(args.number))
    import os
    os.exit(0)

print("\nLoading TTS engine - ignore this...")
sys.stdout.flush()
import tts
print("")
sys.stdout.flush()

prefix = (args.prefix if args.prefix else args.number) + " - "

prompts = client.get_prompts()
for prompt in prompts:
    if prompt['name'].startswith(prefix):
        print("Deleting sound {}".format(prompt['name']))
        sys.stdout.flush()
        client.delete_sound(prompt['id'])
endpoints = client.get_endpoints()
for endpoint in endpoints:
    if endpoint['name'].startswith(prefix):
        print("Deleting endpoint {}".format(endpoint['name']))
        sys.stdout.flush()
        client.delete_endpoint(endpoint['id'])

initial_endpoint_id = None
initial_endpoint_name = None
short_code = args.shortcode
endpoints = []
endpoint_ids = {}
for ii, block in enumerate(blocks):
    text = renderer.render(block)
    headings = [renderer.render(heading) for heading in markdown.get_headings(block)]
    if headings:
        name = headings[0]
    elif ii == 0:
        name = "Initial"
    else:
        print("Disconnected block (no heading) - skipping")
        continue
    links = markdown.get_links(block)
    actions = {}
    for link in links:
        key = list(filter(str.isdigit, renderer.render(link)))
        if key and link.dest.startswith('#'):
            actions[key[0]] = link.dest[1:]
    audio = tts.text_to_speech(text)
    sys.stdout.flush()
    prompt_id = client.create_prompt(prefix + name, audio)
    print("Created prompt {} ({})".format(prefix + name, prompt_id))
    sys.stdout.flush()
    endpoint_id = client.create_ivr_endpoint('{:03d}'.format(short_code), prefix + name, prompt_id)
    print("Created endpoint {} ({})".format(prefix + name, endpoint_id))
    sys.stdout.flush()
    short_code += 1
    endpoints.append((endpoint_id, actions))
    if ii == 0:
        initial_endpoint_id = endpoint_id
        initial_endpoint_name = prefix + name
    for heading in headings:
        endpoint_ids[heading.lower()] = endpoint_id

endpoint_objs = client.get_endpoints()
for endpoint_id, actions in endpoints:
    for endpoint_obj in endpoint_objs:
        if endpoint_obj['id'] == endpoint_id:
            actions = [{"key": key, "action": {"type": "goto", "destination": client.get_endpoint_url(endpoint_ids[actions[key].lower()])}} for key in actions]
            client.update_endpoint_actions(endpoint_obj, actions)
            print("Updated endpoint {} ({})'s actions".format(endpoint_id, endpoint_obj['name']))
            sys.stdout.flush()
            break
    else:
        print("Odd!  Endpoint with ID {} not found, but only created recently?".format(endpoint_id))

client.update_destination(number, initial_endpoint_id)
print("Updated {} to point to endpoint {} ({})".format(args.number, initial_endpoint_name, initial_endpoint_id))
sys.stdout.flush()
