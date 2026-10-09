/** Static AWS service catalog for the architecture studio palette. */

export type ServiceCategory =
  | 'compute'
  | 'storage'
  | 'networking'
  | 'database'
  | 'security'
  | 'integration'
  | 'management'

export interface CatalogService {
  id: string
  name: string
  shortLabel: string
  category: ServiceCategory
  color: string
}

/** Category accent colors (left bar / chip). */
export const CATEGORY_COLORS: Record<ServiceCategory, string> = {
  compute: '#ED7100',
  storage: '#7AA116',
  networking: '#8C4FFF',
  database: '#C925D1',
  security: '#DD344C',
  integration: '#E7157B',
  management: '#E7157B',
}

export const CATEGORY_LABELS: Record<ServiceCategory, string> = {
  compute: 'Compute',
  storage: 'Storage',
  networking: 'Networking',
  database: 'Database',
  security: 'Security',
  integration: 'Integration',
  management: 'Management',
}

/** Catalog ids aligned with backend catalog/aws_services.json */
export const AWS_SERVICES: CatalogService[] = [
  { id: 'ec2', name: 'Amazon EC2', shortLabel: 'EC2', category: 'compute', color: CATEGORY_COLORS.compute },
  { id: 'lambda', name: 'AWS Lambda', shortLabel: 'Lambda', category: 'compute', color: CATEGORY_COLORS.compute },
  { id: 'ecs', name: 'Amazon ECS', shortLabel: 'ECS', category: 'compute', color: CATEGORY_COLORS.compute },
  { id: 'eks', name: 'Amazon EKS', shortLabel: 'EKS', category: 'compute', color: CATEGORY_COLORS.compute },
  { id: 's3', name: 'Amazon S3', shortLabel: 'S3', category: 'storage', color: CATEGORY_COLORS.storage },
  { id: 'api_gateway', name: 'Amazon API Gateway', shortLabel: 'API GW', category: 'networking', color: CATEGORY_COLORS.networking },
  { id: 'alb', name: 'Application Load Balancer', shortLabel: 'ALB', category: 'networking', color: CATEGORY_COLORS.networking },
  { id: 'vpc', name: 'Amazon VPC', shortLabel: 'VPC', category: 'networking', color: CATEGORY_COLORS.networking },
  { id: 'cloudfront', name: 'Amazon CloudFront', shortLabel: 'CloudFront', category: 'networking', color: CATEGORY_COLORS.networking },
  { id: 'rds', name: 'Amazon RDS', shortLabel: 'RDS', category: 'database', color: CATEGORY_COLORS.database },
  { id: 'dynamodb', name: 'Amazon DynamoDB', shortLabel: 'DynamoDB', category: 'database', color: CATEGORY_COLORS.database },
  { id: 'iam', name: 'AWS IAM', shortLabel: 'IAM', category: 'security', color: CATEGORY_COLORS.security },
  { id: 'waf', name: 'AWS WAF', shortLabel: 'WAF', category: 'security', color: CATEGORY_COLORS.security },
  { id: 'secrets_manager', name: 'AWS Secrets Manager', shortLabel: 'Secrets', category: 'security', color: CATEGORY_COLORS.security },
  { id: 'kms', name: 'AWS KMS', shortLabel: 'KMS', category: 'security', color: CATEGORY_COLORS.security },
  { id: 'cognito', name: 'Amazon Cognito', shortLabel: 'Cognito', category: 'security', color: CATEGORY_COLORS.security },
  { id: 'sqs', name: 'Amazon SQS', shortLabel: 'SQS', category: 'integration', color: CATEGORY_COLORS.integration },
  { id: 'sns', name: 'Amazon SNS', shortLabel: 'SNS', category: 'integration', color: CATEGORY_COLORS.integration },
  { id: 'step_functions', name: 'AWS Step Functions', shortLabel: 'Step Fn', category: 'integration', color: CATEGORY_COLORS.integration },
  { id: 'cloudwatch', name: 'Amazon CloudWatch', shortLabel: 'CloudWatch', category: 'management', color: CATEGORY_COLORS.management },
]

const byId = new Map(AWS_SERVICES.map((s) => [s.id, s]))

export function getService(serviceId: string): CatalogService | undefined {
  return byId.get(serviceId)
}

export function getServiceColor(serviceId: string): string {
  return byId.get(serviceId)?.color ?? '#64748b'
}

export function servicesByCategory(): { category: ServiceCategory; label: string; services: CatalogService[] }[] {
  const order: ServiceCategory[] = [
    'compute',
    'storage',
    'networking',
    'database',
    'security',
    'integration',
    'management',
  ]
  return order
    .map((category) => ({
      category,
      label: CATEGORY_LABELS[category],
      services: AWS_SERVICES.filter((s) => s.category === category),
    }))
    .filter((g) => g.services.length > 0)
}
