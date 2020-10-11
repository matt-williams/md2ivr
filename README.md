# md2ivr

md2ivr converts Markdown text (such as this) into a Simwood IVR menu.

For information on requirements, [press 1](#requirements), usage, [press 2](#usage), or for development, [press 3](#development).

## Requirements

You must have a Simwood account, and have created at least one DID number.

If you satisfy these requirements, [press 2](#usage) to continue to usage.

## Usage

md2ivr is run as a docker container.

```
docker build -t md2ivr .
docker run -i --rm md2ivr
```

## Development

md2ivr is written in Python and uses

*   Mozilla TTS
*   marko Markdown-parser
*   requests HTTP client.

