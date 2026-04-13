variable "project_id" {
  description = "New GCP project ID that will host the dev environment."
  type        = string
}

variable "project_number" {
  description = "Numeric GCP project number, used for Workload Identity Federation principal bindings."
  type        = string
}

variable "region" {
  description = "Primary GCP region. Warsaw is close to Bucharest and has GPU-capable zones."
  type        = string
  default     = "europe-central2"
}

variable "zone" {
  description = "Primary GCP zone for the segmentation GPU VM."
  type        = string
  default     = "europe-central2-b"
}

variable "github_owner" {
  description = "GitHub repository owner or organization."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name."
  type        = string
  default     = "car-tuning-ai"
}

variable "database_name" {
  description = "Application database name."
  type        = string
  default     = "car_tuning_dev"
}

variable "database_user" {
  description = "Application database user."
  type        = string
  default     = "car_tuning_app"
}

variable "frontend_image" {
  description = "Initial frontend image. CI/CD replaces this during deploy."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "backend_image" {
  description = "Initial backend image. CI/CD replaces this during deploy."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "segmentation_image" {
  description = "Container image pulled by the segmentation GPU VM."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "segmentation_machine_type" {
  description = "GPU VM machine type."
  type        = string
  default     = "n1-standard-4"
}

variable "segmentation_accelerator_type" {
  description = "GPU type. Confirm quota and exact zone availability before apply."
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "segmentation_accelerator_count" {
  description = "Number of GPUs attached to the segmentation VM."
  type        = number
  default     = 1
}
