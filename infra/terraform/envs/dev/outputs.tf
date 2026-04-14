output "artifact_registry_repository" {
  value = google_artifact_registry_repository.app.name
}

output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}

output "github_deployer_service_account" {
  value = google_service_account.github_deployer.email
}

output "github_workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "models_bucket" {
  value = google_storage_bucket.models.name
}

output "photos_bucket" {
  value = google_storage_bucket.photos.name
}

output "segmentation_private_ip" {
  value = google_compute_instance.segmentation.network_interface[0].network_ip
}
