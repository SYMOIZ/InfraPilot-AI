/** Official AWS Architecture Icons (from aws-icons, based on AWS icon set). */
import AmazonAPIGateway from 'aws-icons/icons/architecture-service/AmazonAPIGateway.svg'
import AmazonCloudFront from 'aws-icons/icons/architecture-service/AmazonCloudFront.svg'
import AmazonCloudWatch from 'aws-icons/icons/architecture-service/AmazonCloudWatch.svg'
import AmazonCognito from 'aws-icons/icons/architecture-service/AmazonCognito.svg'
import AmazonDynamoDB from 'aws-icons/icons/architecture-service/AmazonDynamoDB.svg'
import AmazonEC2 from 'aws-icons/icons/architecture-service/AmazonEC2.svg'
import AmazonElasticContainerService from 'aws-icons/icons/architecture-service/AmazonElasticContainerService.svg'
import AmazonElasticKubernetesService from 'aws-icons/icons/architecture-service/AmazonElasticKubernetesService.svg'
import AmazonRDS from 'aws-icons/icons/architecture-service/AmazonRDS.svg'
import AmazonSimpleNotificationService from 'aws-icons/icons/architecture-service/AmazonSimpleNotificationService.svg'
import AmazonSimpleQueueService from 'aws-icons/icons/architecture-service/AmazonSimpleQueueService.svg'
import AmazonSimpleStorageService from 'aws-icons/icons/architecture-service/AmazonSimpleStorageService.svg'
import AmazonVirtualPrivateCloud from 'aws-icons/icons/architecture-service/AmazonVirtualPrivateCloud.svg'
import AWSIdentityandAccessManagement from 'aws-icons/icons/architecture-service/AWSIdentityandAccessManagement.svg'
import AWSKeyManagementService from 'aws-icons/icons/architecture-service/AWSKeyManagementService.svg'
import AWSLambda from 'aws-icons/icons/architecture-service/AWSLambda.svg'
import AWSSecretsManager from 'aws-icons/icons/architecture-service/AWSSecretsManager.svg'
import AWSStepFunctions from 'aws-icons/icons/architecture-service/AWSStepFunctions.svg'
import AWSWAF from 'aws-icons/icons/architecture-service/AWSWAF.svg'
import ElasticLoadBalancing from 'aws-icons/icons/architecture-service/ElasticLoadBalancing.svg'

/** Vite may resolve SVG imports as URL string or { default: string }. */
function asUrl(mod: string | { default: string }): string {
  return typeof mod === 'string' ? mod : mod.default
}

export const SERVICE_ICON_URLS: Record<string, string> = {
  ec2: asUrl(AmazonEC2),
  lambda: asUrl(AWSLambda),
  s3: asUrl(AmazonSimpleStorageService),
  api_gateway: asUrl(AmazonAPIGateway),
  alb: asUrl(ElasticLoadBalancing),
  rds: asUrl(AmazonRDS),
  dynamodb: asUrl(AmazonDynamoDB),
  vpc: asUrl(AmazonVirtualPrivateCloud),
  iam: asUrl(AWSIdentityandAccessManagement),
  cloudfront: asUrl(AmazonCloudFront),
  sqs: asUrl(AmazonSimpleQueueService),
  sns: asUrl(AmazonSimpleNotificationService),
  cloudwatch: asUrl(AmazonCloudWatch),
  ecs: asUrl(AmazonElasticContainerService),
  eks: asUrl(AmazonElasticKubernetesService),
  step_functions: asUrl(AWSStepFunctions),
  waf: asUrl(AWSWAF),
  secrets_manager: asUrl(AWSSecretsManager),
  kms: asUrl(AWSKeyManagementService),
  cognito: asUrl(AmazonCognito),
}

export function getBuiltinIconUrl(serviceId: string): string | undefined {
  return SERVICE_ICON_URLS[serviceId]
}
