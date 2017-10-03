<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [**BotChehara**](#botchehara)
- [Audience](#audience)
- [The Architecture](#the-architecture)
	- [Slack-bot Installation Flow](#slack-bot-installation-flow)
	- [Slack-bot Event Flow](#slack-bot-event-flow)
		- [Slack Event Handler](#slack-event-handler)
			- [Handling Slack Challenge](#handling-slack-challenge)
			- [Handling Slack Events](#handling-slack-events)
			- [Orchestrator](#orchestrator)
			- [Celebrity Detector](#celebrity-detector)
			- [Landmark Detector](#landmark-detector)
			- [Text Detector](#text-detector)
- [Setup Instructions](#setup-instructions)
	- [Installing Python](#installing-python)
		- [Creating a Python Virtual Environment.](#creating-a-python-virtual-environment)
			- [Initialize your Python Virtual Environment](#initialize-your-python-virtual-environment)
	- [Install Git](#install-git)
	- [Install *BotChehara*](#install-botchehara)
- [Footnotes:](#footnotes)

<!-- /TOC -->﻿

# **BotChehara**


 **BotChehara - The Bot Who Could Not Forget**  

BotChehara is a Slack Bot that recognizes pictures of celebrities, famous landmarks and extracts texts from pictures of documents. *Chehara* is Hindi for Face. BotChehara was inspired by the SMSBot *faces* (see: http://github.com/skarlekar/faces).

BotChehara is 100% Serverless AIaaS<sup>[1](#aiaas)</sup> micro-service built on top of the [Serverless Framework](http://www.serverless.com)  and uses Python, [SlackAPI](https://api.slack.com/), [AWS StepFunctions](https://aws.amazon.com/step-functions), [AWS Rekognition](https://aws.amazon.com/rekognition) and [Google Vision API](https://cloud.google.com/vision). You can invite BotChehara to your [Slack](https://slack.com/) Workspace. Whenever a picture is posted on the invited channel, BotChehara will analyze the picture to identify faces of celebrities, famous landmarks and post the biography or description & map of the landmark back to the channel. If a picture of a scanned document or signage is uploaded, the bot detects text and posts the extracted raw text back to the channel.


# Audience

You are a Developer or Solutions Architect wanting to learn how to build serverless applications that are auto-scaling, pay-per-execution and completely event-driven. You want to build applications that matters to business instead of spending time configuring, deploying and maintaining infrastructure. The boost in efficiency that the Serverless architecture promises is very compelling for you to ignore.

As you are building this application, you will to use the Serverless Framework, Slack Web & Event API,  Boto3 - Amazon's AWS Python SDK and Google Vision API.

----------

# The Architecture

The BotChehara application uses AWS API Gateway, AWS Step Function and Lambdas for compute needs. The Lambdas in turn makes uses of image recognition APIs from AWS & Google Cloud for detecting celebrities, landmarks and text from the given image. The application also uses AWS Dynamo DB for storing data about teams that are inviting the bot to their channels.

As a result,  the application components are provisioned on-demand and brought down after usage resulting in a low-cost, highly-scalable application.

![CheharaBot Architecture Diagram](https://github.com/skarlekar/chehara/blob/master/Resources/BotCheharaArchitecture.png)

The above picture illustrates the high-level architecture of the application. Details are as follows:

## Slack-bot Installation Flow

The following sequence diagram illustrates the Slack-bot Installation flow. This flow is also illustrated using red color arrows in the architecture diagram above.

![Installation Flow Sequence Diagram](https://github.com/skarlekar/chehara/blob/master/Resources/Installation%20Flow.png)
1. To use our bot, the user has to be install the bot in their Slack Workspace.

2. Installation begins when the user clicks the *#Add to Slack* button in the installation page.

3. When the user installs our slack bot in their workspace, Slack will send a temporary authorization code. This authorization code is short-lived and can only be used to get a permanent access token.

4. The *Slack Installer* Lambda function will use this authorization code to get a permanent access-token for the team along with other pertinent information regarding the team and store it in a Dynamo DB table.

5. If the operation is successful,  the Lambda returns a 302 HTTP code and success code to have Slack redirect the user to a success page.

6. On the other hand, if the operation fails, the Lambda returns a 302 HTTP code and failure code to have Slack redirect the user to an error page.

## Slack-bot Event Flow

The following sequence diagram depicts the event flow process. The event processing flow is also depicted using the blue color arrows in the above architecture diagram and consists of multiple steps as described below:

![BotChehara Event Flow Sequence Diagram](https://github.com/skarlekar/chehara/blob/master/Resources/EventHandlerFlowFull.png)

### Slack Event Handler

The *Slack Event Handler* is a Lambda function that handles URL verifications and other events from Slack.

To get notified of events happening in the channels that our bot is invited to,  our bot application on Slack will be configured with an event handler endpoint. Event sent to this endpoint is handled by Slack Event Handler.

#### Handling Slack Challenge

1. Before using our URL endpoint to send events that our bot is subscribed to, Slack will verify if the URL is valid and belongs to us by sending a challenge token in the body of the request. The Slack Event Handler responds to the challenge by sending back the challenge token in the response.

2. Additionally, every event notification from Slack contains a verification token. The Slack Event Handler confirms that this verification token belongs to the bot by comparing the verification token that was sent with a private verification token that it was preconfigured with.

3. Irrespective of the type of event, Slack expects a 200-OK response to any event that it is notified of at the endpoint within three seconds.

#### Handling Slack Events

1.  The Slack bot is subscribed to all messages that is being communicated on the channel the bot is invited to. As the bot is only interested in file uploads, it will filter out all other messages and only handle messages that is a result of a file share.

2.  As image detection may run over the three second time limit, the bot invokes a step function asynchronously to process the filtered events before returning the 200-OK response.

#### Orchestrator

The Orchestrator is a StepFunction that farms out the detection of content in the image to various image content detectors. Right now, the bot can detect celebrities, landmarks and text in the given image. The image content detectors are  Lambda functions that employs various AIaaS service such as Google Vision and AWS Rekognition.

One of the advantages of using the Step Function here is, you can add new type of detectors in a plug-n-play fashion. For instance, you can add a detector to detect your friends in images. Hint: Review the [CelebritySleuth](https://github.com/skarlekar/faces) project to figure out how to do this.

<p align="center">
  <img src="https://github.com/skarlekar/chehara/blob/master/Resources/CheharaStepFunction.png" alt="Step Function Detail"/>
</p>

#### Celebrity Detector

For detecting Celebrities, the bot employs AWS Rekogniton. Amazon Rekognition is a service that makes it easy to add image analysis to your applications. With Rekognition, you can detect objects, scenes, and faces in images. You can also search and compare faces.

The Celebrity Detector uses a Lambda function to call the AWS Rekognition service with the right credentials to get a report of the image content. If the image does not contain a face, or if the face is not a recognized face, the result is discarded.

On the other hand, if a face of a celebrity is detected, it gets the name of the celebrity, the confidence in the match and biography URL to construct the report.

The event is then enriched with this content and passed down through the Step Function.

Note: In my testing, only Azure Vision and AWS Rekognition is able to detect celebrities without training. As of this writing, Google Vision is not able to do that.

#### Landmark Detector

When given an image of a famous landmark, AWS Rekognition will detect it as a monument or architecture, but it is not able to pin point the name of the landmark. This is where Google Vision shines through. Google Vision can not only pin point the landmark, it also provides the geo location of the landmark.

The Landmark Detector in this bot is a Lambda function that calls Google Vision API with an API key  and image contents to get the report.

If the report contains landmark information, it extracts the data and constructs a report. The input event is then enriched with the report and the content is passed down through the Step Function.

#### Text Detector

Similar to the landmark detection, Google Vision is the only viable AIaaS service that I found that can detect text, recognize characters and construct the sentence. In my testing, I found that Google Vision is not able to recognize text in languages other than English.

Similar to the other detectors, the Text Detector in this bot is a Lambda function that calls Google Vision API with an API key and image contents to get the report.

If the report contains text information, it will extract the text and  enrich the input event with the report. This event is then passed down the chain in the Step Function.

**Findings**: In my testing I found the following drawbacks in the Google Vision service for detecting text:

1. Google Vision is not able to recognize text in languages other than English.
2. Google Vision fails to detect text if the text content is skewed. ie., the text has to be laid out horizontally in the image.
3. Some images contain extraneous text that is not visible to the naked eye. This data comes out as textual content which has beleaguered me. Could this be watermark data? I could not tell.

# Setup Instructions

## Installing Python
If you are on a Mac or Linux machine, you probably already have Python installed. On Windows you have to install Python.

Regardless of your operating system, you are better off using a virtual environment for running Python. [Anaconda](https://www.continuum.io/downloads) or its terse version [Miniconda](https://conda.io/miniconda.html) is a Python virtual environment that allows you to manage various versions and environments of Python. The installers come with Python and the package manager *conda* with it. Follow the instructions [here](https://conda.io/docs/install/quick.html) to install Miniconda. For this project we will use Python 2.7.

### Creating a Python Virtual Environment.
After installing Python 2.7, create an virtual environment as follows. Note:  I am calling my virtual environment *chehara*:

    $ conda create -n chehara python=2

#### Initialize your Python Virtual Environment
To start working in your new Python virtual environment:

    $ source activate chehara

If you are working in Windows, use:

    $ activate chehara

## Install Git
Git is a popular code revision control system. To install Git for your respective operating system follow the instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

## Install *BotChehara*
To install BotChehara from Git, follow the instructions below:

    $ mkdir DevFestDC
    $ cd DevFestDC
    $ git clone --recursive https://github.com/skarlekar/chehara.git


# Footnotes:
<a name="aiaas">1</a>: AIaaS - Artificial Intelligence as a Service is a packaged, easy-to-use cognitive service offered by many leading cloud providers to perform natural language processing, image recognition, speech synthesis and other services that involves artificial intelligence. To use these services you don't have to be an expert on artificial intelligence or machine learning skills.

More documentation to follow soon.