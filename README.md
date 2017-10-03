

# **BotChehara**


 **BotChehara - The Bot Who Could Not Forget**  

BotChehara is a Slack Bot that recognizes pictures of celebrities, famous landmarks and extracts texts from pictures of documents. *Chehara* is Hindi for Face. BotChehara was inspired by the SMSBot *faces* (see: http://github.com/skarlekar/faces). 

BotChehara is 100% Serverless AIaaS[^aiaas] micro-service built on top of the [Serverless Framework](http://www.serverless.com)  and uses Python, [SlackAPI](https://api.slack.com/), [AWS StepFunctions](https://aws.amazon.com/step-functions), [AWS Rekognition](https://aws.amazon.com/rekognition) and [Google Vision API](https://cloud.google.com/vision). You can invite BotChehara to your [Slack](https://slack.com/) Workspace. Whenever a picture is posted on the invited channel, BotChehara will analyze the picture to identify faces of celebrities, famous landmarks and post the biography or description & map of the landmark back to the channel. If a picture of a scanned document or signage is uploaded, the bot detects text and posts the extracted raw text back to the channel.


# Audience

You are a Developer or Solutions Architect wanting to learn how to build serverless applications that are auto-scaling, pay-per-execution and completely event-driven. You want to build applications that matters to business instead of spending time configuring, deploying and maintaining infrastructure. The boost in efficiency that the Serverless architecture promises is very compelling for you to ignore.

As you are building this application, you will to use the Serverless Framework, Slack Web & Event API,  Boto3 - Amazon's AWS Python SDK and Google Vision API.

----------

# The Architecture

The BotChehara application uses AWS API Gateway, AWS Step Function and Lambdas for compute needs. The Lambdas in turn makes uses of image recognition APIs from AWS & Google Cloud for detecting celebrities, landmarks and text from the given image. The application also uses AWS Dynamo DB for storing data about teams that are inviting the bot to their channels. 

As a result,  the application components are provisioned on-demand and brought down after usage resulting in a low-cost, highly-scalable application.

![enter image description here](https://github.com/skarlekar/chehara/blob/master/Resources/BotCheharaArchitecture.png)

The above picture illustrates the high-level architecture of the application. Details are as follows:

## Slack-bot Installation Flow

This flow is illustrated using red color arrows in the diagram above.

![Installation Flow Sequence Diagram](https://github.com/skarlekar/chehara/blob/master/Resources/Installation%20Flow.png)
1. To use our bot, the user has to be install the bot in their Slack Workspace. 

2. Installation begins when the user clicks the *#Add to Slack* button in the installation page.

3. When the user installs our slack bot in their workspace, Slack will send a temporary authorization code. This authorization code is short-lived and can only be used to get a permanent access token. 

4. The *Slack Installer* Lambda function will use this authorization code to get a permanent access-token for the team along with other pertinent information regarding the team and store it in a Dynamo DB table. 

5. If the operation is successful,  the Lambda returns a 302 HTTP code and success code to have Slack redirect the user to a success page. 

6. On the other hand, if the operation fails, the Lambda returns a 302 HTTP code and failure code to have Slack redirect the user to an error page. 
 
## Slack-bot Event Flow

The event processing flow is depicted using the blue color arrows in the above architecture diagram and consists of multiple steps as described below:

### Slack Event Handler

The *Slack Event Handler* is a Lambda function that handles URL verifications and other events from Slack.

To get notified of events happening in the channels that our bot is invited to,  our bot application on Slack will be configured with an event handler endpoint. Event sent to this endpoint is handled by Slack Event Handler. 

![Event Flow Sequence Diagram](https://github.com/skarlekar/chehara/blob/master/Resources/EventHandlerFlowFull.png)

#### Handling Slack Challenge 

1. Before using our URL endpoint to send events that our bot is subscribed to, Slack will verify if the URL is valid and belongs to us by sending a challenge token in the body of the request. The Slack Event Handler responds to the challenge by sending back the challenge token in the response.

2. Additionally, every event notification from Slack contains a verification token. The Slack Event Handler confirms that this verification token belongs to the bot by comparing the verification token that was sent with a private verification token that it was preconfigured with.

3. Irrespective of the type of event, Slack expects a 200-OK response to any event that it is notified of at the endpoint within three seconds. 

#### Handling Slack Events

1.  The Slack bot is subscribed to all messages that is being communicated on the channel the bot is invited to. As the bot is only interested in images, it will filter out all other messages and only handle messages that contains an image.
 
2.  As image detection may run over the three second time limit, the bot invokes a step function asynchronously to process the events before returning the 200-OK response.


[^aiaas]: AIaaS - Artificial Intelligence as a Service is a packaged, easy-to-use cognitive service offered by many leading cloud providers to perform natural language processing, image recognition, speech synthesis and other services that involves artificial intelligence. To use these services you don't have to be an expert on artificial intelligence or machine learning skills.

More documentation to follow soon.
