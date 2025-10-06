output "chat_public_dns" { value = module.svc_chat.public_dns }
output "chat_private_ip" { value = module.svc_chat.private_ip }

output "url" {
  value       = "http://${module.svc_chat.public_dns}/health"
  description = "Probar /health o /docs"
}
