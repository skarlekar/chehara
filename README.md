

# **BotChehara**


**BotChehara - The Bot Who Could Not Forget. **

BotChehara is a Slack Bot that recognizes pictures of celebrities, famous landmarks and extracts texts from pictures of documents. Chehara is Hindi for Face. BotChehara was inspired by the SMSBot *faces* (see: http://github.com/skarlekar/faces). 

BotChehara is 100% Serverless AIaaS[^aiaas] micro-service built on top of the Serverless Framework (see: http://www.serverless.com) and uses Python, SlackAPI, AWS StepFunctions, AWS Rekognition and Google Vision API. You can invite BotChehara to your Slack Workspace. Whenever a picture is posted on the invited channel, BotChehara will analyze the picture to identify faces of celebrities, famous landmarks and post the biography or description & map of the landmark back to the channel. If a picture of a scanned document or signage is uploaded, the bot detects text and posts the extracted raw text back to the channel.


# Audience

You are a Developer or Solutions Architect wanting to learn how to build serverless applications that are auto-scaling, pay-per-execution and completely event-driven. You want to build applications that matters to business instead of spending time configuring, deploying and maintaining infrastructure. The boost in efficiency that the Serverless architecture promises is very compelling for you to ignore.

As you are building this application, you will to use the Serverless Framework, Slack Web & Event API,  Boto3 - Amazon's AWS Python SDK and Google Vision API.

----------


[^aiaas]: AIaaS - Artificial Intelligence as a Service is a packaged, easy-to-use cognitive service offered by many leading cloud providers to perform natural language processing, image recognition, speech synthesis and other services that involves artificial intelligence. To use these services you don't have to be an expert on artificial intelligence or machine learning skills.

More documentation to follow soon.
