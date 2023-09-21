# XENON J.A.R.V.I.S Slack HelpDesk API 

<img src="/static/images/Color_logo_no_background.svg" alt="XENON J.A.R.V.I.S Dashboard Logo" width="200" height="200">

XENON J.A.R.V.I.S is a Slack API integrated with Flask, designed to streamline the HelpDesk process and enhance user experience for the [XENON International Collaboration](https://xenonexperiment.org). Report issues, get insights, and receive guidance, all within the Slack environment. In this repository we, for now, only describe how to run the application for devlopment purposes (not production).

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Installation

1. Create Your Slack Application on [Slack API](https://api.slack.com/apps) (set-up App name and provides permissions as indicated in [Configuration](#configuration)).

2. Set up the MongoDB 

This tools requires an access to a MongoDB collection. You can set-up one for free with [MongoDB Atlas](https://cloud.mongodb.com).

```
git clone https://github.com/DonNabla/XenonJarvis.git
```

3. Deploy your Slack API on a DigitalOcean 

[DigitalOcean App platform](https://cloud.digitalocean.com/apps?i=236303)

## Usage

1. Set up your environment variables during the deployement of your Application on DigitalOcean. This project requires the following:

- `SLACK_SIGNING_SECRET` From [Slack API](https://api.slack.com/apps)
- `SLACK_BOT_TOKEN` From [Slack API](https://api.slack.com/apps)
- `CHANNEL_ID` From Slack client
- `MONGODB_USERNAME` From [MongoDB Atlas](https://cloud.mongodb.com)
- `MONGODB_PASSWORD` From [MongoDB Atlas](https://cloud.mongodb.com)
- `MONGODB_DATABASE` From [MongoDB Atlas](https://cloud.mongodb.com)


2. You can edit/remove/add the issues list and instructions in the instructions repository directly


3. Interact with the API through Slack and view the dashboard by navigating to the `/dashboard` route.

## Configuration

To run properly, your slack application needs to have Interactivity option turned on and the following permissions granted (settings in [Slack API](https://api.slack.com/apps)):

- `chat:write`
- `chat:write.public`
- `commands`
- `users:read`

For the Interactivity option, it will request an URL (such as `https://NameOfAppSite.ondigitalocean.app/slack/interactions`) to send the HTTP POST request induced by interaction triggered by users on SLACK.

On the MongoDB side, you need to add your digitalocean machine IP address to the IP access list in MongoDB Atlas.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Acknowledgments

- Thanks to everyone who provided feedback and contributed to the project.
- Special mention to [OpenAI](https://www.openai.com/) for assistance with various components.
