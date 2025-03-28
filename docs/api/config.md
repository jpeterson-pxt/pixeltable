# Pixeltable Configuration

Pixeltable configuration options can be specified in one of two ways:

- Using environment variables, such as `PIXELTABLE_HOME` and `OPENAI_API_KEY`; and/or
- In the system configuration file `$PIXELTABLE_HOME/config.toml` (usually `~/.pixeltable/config.toml`).

The system configuration file follows the usual TOML format with headings and values:

```toml
[pixeltable]
file_cache_size_g = 250

[openai]
api_key = 'my-openai-api-key'

[label_studio]
url = 'http://localhost:8080/'
api_key = 'my-label-studio-api-key'
```

Most options can be specified either as an environment variable or in `config.toml`,
although a few can only be specified as an environment variable. It is fine for some options to be given as environment
variables and others in `config.toml`. If a configuration parameter is specified both ways,
the environment variable will be used preferentially.

## System Configuration

| Environment Variable         | Config File                       | Meaning                                                                                                                                     |
|------------------------------|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| PIXELTABLE_HOME              |                                   | (string) Pixeltable user directory; default is `~/.pixeltable` |
| PIXELTABLE_CONFIG            |                                   | (string) Pixeltable config file; default is `$PIXELTABLE_HOME/config. |
| PIXELTABLE_PGDATA            |                                   | (string) Directory where Pixeltable DB is stored; default is `$PIXELTABLE_HOME/pgdata` |
| PIXELTABLE_DB                |                                   | (string) Pixeltable database name; default is `pixeltable` |
| PIXELTABLE_API_KEY           | [pixeltable]<br>api_key           | (string) API key for Pixeltable Cloud |
| PIXELTABLE_FILE_CACHE_SIZE_G | [pixeltable]<br>file_cache_size_g | (float) Maximum size of the Pixeltable file cache, in GiB; required |
| PIXELTABLE_HIDE_WARNINGS     | [pixeltable]<br>hide_warnings     | (bool) Suppress warnings generated by various libraries used by Pixeltable; default is `false` |
| PIXELTABLE_TIME_ZONE         | [pixeltable]<br>time_zone         | (string) Default time zone in [IANA format](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones); defaults to the system time zone |
| PIXELTABLE_VERBOSITY         | [pixeltable]<br>verbosity         | (int) Verbosity level for Pixeltable console output (`0` = warnings only, `1` = normal, `2` = verbose); default is `1` |

## APIs

| Environment Variable | Config File | Meaning |
|-|-|-|
| ANTHROPIC_API_KEY | [anthropic]<br>api_key | (string) API key to use for Anthropic services |
| FIREWORKS_API_KEY | [fireworks]<br>api_key | (string) API key to use for Fireworks AI services |
| GEMINI_API_KEY | [gemini]<br>api_key | (string) API key to use for Google Gemini services |
| LABEL_STUDIO_API_KEY | [label_studio]<br>api_key | (string) API key to use for Label Studio |
| LABEL_STUDIO_URL | [label_studio]<br>url | (string) URL of the Label Studio server to use |
| MISTRAL_API_KEY | [mistral]<br>api_key | (string) API key to use for Mistral AI services |
| OPENAI_API_KEY | [openai]<br>api_key | (string) API key to use for OpenAI services |
| REPLICATE_API_TOKEN | [replicate]<br>api_token | (string) API token to use for Replicate services |
| TOGETHER_API_KEY | [together]<br>api_key | (string) API key to use for Together AI services |
