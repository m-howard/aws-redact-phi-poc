# AWS Redact PHI POC

This POC uses the serveless framework to show a brute force way to redact PHI from documents, using the AWS services - Textract and Comprehend Medical.

## Deploying Service
### Requirements
* [Docker](https://docs.docker.com/get-docker/)
* [virtualenv with Python 3](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
* [Serverless](https://www.serverless.com/framework/docs/providers/aws/guide/installation/)

### Running 
```
$ serverless deploy
```