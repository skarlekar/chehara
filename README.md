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
	- [Install ObjectPath](#install-objectpath)
		- [Testing ObjectPath](#testing-objectpath)
		- [Using ObjectPath](#using-objectpath)
	- [Setup Amazon AWS](#setup-amazon-aws)
	- [Install node.js and Serverless framework](#install-nodejs-and-serverless-framework)
	- [Testing your Serverless Setup](#testing-your-serverless-setup)
	- [Setup Google Cloud](#setup-google-cloud)
	- [Setup Slack](#setup-slack)
		- [Create a Slack Work Space](#create-a-slack-work-space)
		- [Create a Slack App](#create-a-slack-app)
		- [Add a Slack Bot User](#add-a-slack-bot-user)
		- [Create an Add to Slack Button](#create-an-add-to-slack-button)
	- [Build & Deploy BotChehara](#build-deploy-botchehara)
	- [Add Install URL to Slack](#add-install-url-to-slack)
	- [Test *#Add to Slack* Function](#test-add-to-slack-function)
	- [Configure Event Webhook](#configure-event-webhook)
		- [Permission Scope](#permission-scope)
		- [Enable Events](#enable-events)
		- [Invite Bot](#invite-bot)
- [Using BotChehara](#using-botchehara)
- [Application in Action](#application-in-action)
	- [Celebrity Detection Example](#celebrity-detection-example)
	- [Landmark Detection Example](#landmark-detection-example)
	- [Text Detection Example](#text-detection-example)
- [Footnotes](#footnotes)

<!-- /TOC -->

# **BotChehara**


 **BotChehara - The Bot Who Could Not Forget**  

BotChehara is a Slack Bot that recognizes pictures of celebrities, famous landmarks and extracts texts from pictures of documents. *Chehara* is Hindi for Face. BotChehara was inspired by the SMSBot *faces* (see: http://github.com/skarlekar/faces).

BotChehara is 100% Serverless AIaaS<sup>[1](#aiaas)</sup> micro-service built on top of the [Serverless Framework](http://www.serverless.com)  and uses Python, [SlackAPI](https://api.slack.com/), [AWS StepFunctions](https://aws.amazon.com/step-functions), [AWS Rekognition](https://aws.amazon.com/rekognition) and [Google Vision API](https://cloud.google.com/vision). You can invite BotChehara to your [Slack](https://slack.com/) Workspace. Whenever a picture is posted on the invited channel, BotChehara will analyze the picture to identify faces of celebrities, famous landmarks and post the biography or description & map of the landmark back to the channel. If a picture of a scanned document or signage is uploaded, the bot detects text and posts the extracted raw text back to the channel.


# Audience

You are a Developer or Solutions Architect wanting to learn how to build serverless applications that are auto-scaling, pay-per-execution and completely event-driven. You want to build applications that matters to business instead of spending time configuring, deploying and maintaining infrastructure. The boost in efficiency that the Serverless architecture promises is very compelling for you to ignore.

As you are building this application, you will learn to use the Serverless Framework, Slack Web & Event API,  ObjectPath, Boto3 - Amazon's AWS Python SDK and Google Vision API.

----------

# The Architecture

The BotChehara application uses AWS API Gateway, AWS Step Function and Lambdas for compute needs. The Lambdas in turn makes uses of image recognition APIs from AWS & Google Cloud for detecting celebrities, landmarks and text from the given image. The application also uses AWS Dynamo DB for storing data about teams that are inviting the bot to their channels.

As a result,  the application components are provisioned on-demand and brought down after usage resulting in a low-cost, highly-scalable application.

![CheharaBot Architecture Diagram](https://github.com/skarlekar/chehara/blob/master/Resources/BotCheharaArchitecture.png)

The above picture illustrates the high-level architecture of the application. Details are as follows:

## Slack-bot Installation Flow

The following sequence diagram illustrates the Slack-bot Installation flow. This flow is also illustrated using red color arrows in the architecture diagram above.

![Installation Flow Sequence Diagram](https://github.com/skarlekar/chehara/blob/master/Resources/InstallationFlow.png)

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


----------


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

## Install ObjectPath
ObjectPath is a JSON query language and tool. To install ObjectPath, follow the instructions below:

    $pip install objectpath

### Testing ObjectPath
If ObjectPath is correctly installed in your Python virtual environment, when you type ObjectPath in your command line, you should see the interactive environment as follows:

    srini-macbookpro:chehara skarlekar$ objectpath ObjectPath interactive shell ctrl+c to exit, documentation at http://adriank.github.io/ObjectPath.

    JSON document source not specified. Working with an empty object {}.
    >>>

Exit by pressing Control-C.

### Using ObjectPath
You can use ObjectPath using the ObjectPath libraries in your Python code or test your JSON queries in the interactive shell.

Let us try an example. I have checked in a file call *book-shop.json*. Let us use that to practice some simple queries.

At the command prompt, enter:

    $ objectpath book-shop.json

This should take you to the interactive shell with the book-shop.json as the input document. Let us try a few queries:

Simple queries starts with $ character. It indicates the root of the document. To show the whole document type:

    $*

ObjectPath is like paths to files in your operating system. To show only the *book* fragment under the *store*, type:

    $.store.book

You can select a specific element from it as follows:

    $.store.book[1] # get the second book. Why?
    $.store.book[-1] # get the last book. How?

We can also get specific elements based on their properties:

    $.store.book[@.price is 8.95] # get books of price 8.95

Here ***@*** points to the current element from books. In other words, ***[*** iterates over the array of books and for each element checks if condition inside square parenthesis is met. ***@*** tells ObjectPath that price is an property of each book, not a string.

To make it even more interesting we can filter it even further by getting only the specific fields from results:

    $.store.book[@.price is 8.95].(price, author)

When we don't know where in the document are prices, we can search for all of them by:

    $..price # searches for any attribute named price in the document
    $..price[@ > 8.95] # returns all prices greater than 8.95

In the last example we used @ to indicate current element of an array of prices.

You can also create new JSON documents as shown below:

    { 'fictions' : $.store.book[@.category is 'fiction'] }

This should create a new fictions JSON and populate it with books whose category is fiction.

For further reference, go to [ObjectPath](http://objectpath.org/reference.html) documentation.

## Setup Amazon AWS
1. Sign into your AWS account or [sign-up](https://console.aws.amazon.com/console/home?region=us-east-1) for one.

2. Setup your AWS credentials by following the instructions from [here](https://serverless.com/framework/docs/providers/aws/guide/credentials/).

## Install node.js and Serverless framework
Serverless framework is a node.js application. To use Serverless framework and run the CelebritySleuth application you need to install node.js. Follow the [instructions](https://serverless.com/framework/docs/providers/aws/guide/installation/) from Serverless website to install both node.js and the Serverless framework.

Ensure your Serverless framework is operational using the following:

    $ serverless --version

## Testing your Serverless Setup
Now that you have setup AWS, it is time to test your Serverless setup by creating a mock function using the Serverless framework.

Create a test directory. In the test directory, create a Lambda function from the default template as follows:

    $ mkdir sls-tester
    $ cd sls-tester
    $ sls create --template aws-python --name sls-test

This should create two files in the current directory:

> serverless.yml
>
> handler.py

The *serverless.yml* declares a sample service and a function. The *handler.py*  returns a message stating that your function executed successfully.

To deploy the function, simply type:

    $ sls deploy --verbose

This should deploy the function. The verbose option provides extra information.

To test your function, type:

    $ sls invoke --function hello

If you get the following message, your Serverless setup is working.

      WARNING: You are running v1.9.0. v1.10.0 will include the following breaking changes:
        - Some lifecycle events for the deploy plugin will move to a new package plugin. More info -> https://git.io/vy1zC

      You can opt-out from these warnings by setting the "SLS_IGNORE_WARNING=*" environment variable.

    {
        "body": "{\"input\": {}, \"message\": \"Go Serverless v1.0! Your function executed successfully!\"}",
        "statusCode": 200
    }

To check the logs for your function, type:

    $ sls logs -f hello

To keep a continuous check of the logs for your function, type:

    $ sls logs -f hello -t

## Setup Google Cloud

1. Sign up for a new Google account at http://accounts.google.com. If you already have an account you can skip this step.
2. Sign up for a Google Cloud trial at http://console.cloud.google.com/start. If you already have Google Cloud privileges on  your Google account, you can skip this step.
3. Create a new project and call it BotProject.
4. Select *Credentials* in *API & Services* section of the Google Cloud console.
5. Under *Create Credentials*, create a new API key. **Make a note of this API key as you will need that in subsequent steps**.
6. In the *API & Services* dashboard, enable *Google Cloud Vision API*.

## Setup Slack

### Create a Slack Work Space
1. Go to https://slack.com/create#email and sign-up for a new workspace by entering in your email address.
2. Confirm your email by entering the six-digit confirmation code sent to your email address.
3. Provide your name and reason you are creating a workspace.

<p align='center'> <img src='https://github.com/skarlekar/chehara/blob/master/Resources/Slack-signup-1.png'/> </p>

4. Provide a name for your group. This name will be use to name your Slack workspace.
<p align='center'> <img src='https://github.com/skarlekar/chehara/blob/master/Resources/Slack-signup-2.png'/> </p>

5. Choose an address you will use to sign into Slack. Note this down as you will use this to access your slack workspace.
<p align='center'> <img src='https://github.com/skarlekar/chehara/blob/master/Resources/Slack-signup-3.png'/> </p>

6. Skip the Invite section.

Congratulations, your workspace is ready.

### Create a Slack App
To start using Slack's API, create a Slack App. This will provide us the tokens necessary for communicating with Slack. The following steps walks you through the process.

1. Go to you Slack workspace using and click the dropdown next to your Slack workspace name.

2. Select *Manage Apps* in the menu dropdown next to your Slack workspace name.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Build-app-1.png)

3. In the *Manage Apps* page, click on *Build* to build a new application.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Build-app-2.png)

4. In the *Build* page, click on *Start Building* button.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Build-app-3.png)

5. In the *Create a Slack App* form, enter a name for your bot under the *App Name* field.

6. In the Development Slack Workspace field, select the name of your workspace.

7. Click on *Create App* to create your Slack application.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Build-app-4.png)

8. Once your Slack app is created, it is time to make note of your application credentials under the App Credentials section. Use this information to update the [setEnv.sh](https://github.com/skarlekar/chehara/blob/master/setEnv.sh) file.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Build-app-5.png)

9. Install a 512x512 size PNG file as icon for your bot in the *Display Information* section.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Build-app-7.png)

10. Note: Do not click on *Distribute App* in the *Manage Distribution* section. We will do this using a custom button to manage the OAuth process.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Build-app-6.png)

Congratulations for creating your Slack application and obtaining its credentials.

### Add a Slack Bot User
For the application to interact with our users in a conversation, we have to add a bot that will be managed from the cloud.  To do this we will add a Bot User to our application.  

Follow the instructions below to add the Bot User:

1. Make sure you are in the *apps* section of Slack.

2. Choose the app created in the section above.

3. Click on *Bot Users* in the side bar menu.

4. In the *Bot User* page, click on *Add a Bot User* button.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Install-Bot-User-1.png)

5. In the following page, the Display name and Default username comes pre-filled.

6. Click on *Add Bot User* to add a bot to your application.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Install-Bot-User-2.png)

You have now associated a Bot User to your app. This Bot User will be the brain of your app.

### Create an Add to Slack Button
For users to invite our Bot to their channels and have the Bot talk to our service on the cloud in a secure manner using OAuth, we will have to create a button and a web-page. This button will then be used by our users to install the Bot in their workspace and invite our Bot into their channels.

1. Let us start by clicking on *Your Apps* page to ensure that you are in http://api.slack.com/apps page.

2. Scroll down to the Authentication section of this page.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Add-to-Slack-Button-1.png)

3. Click on the *Slack Button*. This will take us to the API docs for the Slack button.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Add-to-Slack-Button-2.png)

4. Scroll down to the *Add the Slack Button* section of the page. Ensure that the name of your Bot is selected in the Drop-down.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Add-to-Slack-Button-3.png)

5. Ensure that only the *bot* button is checked.

6. Copy the code snippet that contains your client id.

7. Go to the [slack-install-site/index.html](https://github.com/skarlekar/chehara/blob/master/slack-install-site/index.html) web-page and replace the section from line 30-34 with the copied code snippet.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Add-to-Slack-Button-4.png)

8. Create a S3 bucket and prepare it for static website hosting.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Add-to-Slack-Button-5.png)

9. Install this website in a S3 bucket of your choice and make sure that the S3 bucket is configured to serve as a website.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/Add-to-Slack-Button-6.png)

10. Make a note of the public URL for the *index.html* in your S3 bucket.

11. In your serverless.yml file update the *INSTALL_SUCCESS_URL* and *INSTALL_ERROR_URL* with the path to your *index.html*. Add *#success* at the end of the Success URL and *#error* at the end of the Error URL as shown below.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/serverless-yml-1.png)

## Build & Deploy BotChehara

Now that the preliminary configuration of Slack is done, it is time to build and deploy our Bot.

1. Open a terminal and go to the root of the repository where our Git is cloned.

2. Ensure the *setEnv.sh* is updated with the proper credentials. Now export you environment variables:

    source ./setEnv.sh

3.  Type the following in the command prompt to build and deploy our services to AWS cloud.

    sls deploy --verbose

4. You should get an output that should state that the service was successfully published as shown below.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/build-and-deploy-chehara-1.png)

5. Note down the Install endpoint which uses HTTP GET.

## Add Install URL to Slack
1. With the install endpoint stashed in your clipboard, go to the *OAuth & Permissions* setting of your Slack App.

2. In the *Redirect URLs* section, select *Add a new Redirect URL* and paste your install URL. Click on *Add* button.

3. Finally, click on *Save URLs* to save the setting.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/install-url-1.png)

## Test *#Add to Slack* Function
1. To test the *#Add to Slack* functionality, you can either go to the *index.html* in your *slack-install-site* that you pushed to the S3 bucket or go the slack-button docs page as shown below.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/test-add-to-slack-1.png)

2. This should take you to a page where you authorize and confirm the identity of the Bot user you created earlier.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/test-add-to-slack-2.png)

3. If everything goes well, you should see a success message.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/test-add-to-slack-3.png)

4. You can now verify that your Bot user is added to your workspace. Go to your workspace and under Apps, you should see the Bot user you created.

 ![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/test-add-to-slack-4.png)

5. You can also check the Lambda logs in your Serverless project directory at the command prompt by typing:

    serverless logs -f installSlack

6. In addition you can go to your DynamoDB table and verify a new Item was created in the *slack teams* table.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/test-add-to-slack-5.png)

## Configure Event Webhook
For Slack to send notify the bot with events in the channels that it subscribed to, the following must happen:

1. Set Permission Scope: Configure the Slack APIs the bot is allowed to use.
2. Set Event Subscriptions: Indicate which events that Slack will notify to the bot.
3. Invite Bot: Invite the bot to a channel to initiate conversation.  

### Permission Scope
1. In the *OAuth & Permissions* section of your App,  got the *Scopes* section. In the *Select Permission Scopes* dropdown choose the following:

	1. *Send Messages as your-bot-name*
	2. *Access the workspace’s files, comments, and associated information*

2. Click the *Save Changes* button. You will get a notification to reinstall your app. Click the notification to reinstall your app and authorize the change. Your configuration should look like:

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/configure-web-event-1.png)

### Enable Events
1. From your command line where you built & deployed the serverless framework, copy the POST method. This is the URL that ends with '*events*'.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/enable-events-1.png)

2. Go to the *Event Subscriptions* section of your app and turn *Enable Events* to *on*.

3. Paste the events URL in the *Request URL* field.

4. Slack will immediately verify the URL. If everything goes well, you should get a *verified* confirmation.

5. In the *Subscribe to Bot Events* section, select the *message.channels ev*ent.

6. Make sure you click on the *Save Changes* button.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/enable-events-2.png)

### Invite Bot
For your bot to be useful, you must invite the bot into a channel. For this exercise we will invite the bot in the General channel in your workspace by typing:

    /invite @name-of-your bot

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/invite-bot-1.png)


----------


# Using BotChehara
You are now ready to start using the bot.

Go to the general channel in your Slack workspace. Upload or drag and drop a picture into the channel.  Witness the magic of your bot.

If the image has a picture of a well-known celebrity you will get their names and link to their biography. If there are famous landmarks, you should get the name of the landmark and a Google map link along with it.

**Caution**: Make sure your image size is lesser than 5MB. Most of the cognitive services does not accept large images.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/bot-usage-1.png)


----------


# Application in Action
The following are some examples of the application in action.

## Celebrity Detection Example

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/app-in-action-1.gif)


## Landmark Detection Example

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/app-in-action-2.gif)


## Text Detection Example

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/app-in-action-3.gif)

----------


# Footnotes

<a name="aiaas">1</a>: AIaaS - Artificial Intelligence as a Service is a packaged, easy-to-use cognitive service offered by many leading cloud providers to perform natural language processing, image recognition, speech synthesis and other services that involves artificial intelligence. To use these services you don't have to be an expert on artificial intelligence or machine learning skills.
