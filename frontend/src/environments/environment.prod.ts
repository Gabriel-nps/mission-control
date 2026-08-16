export const environment = {
  production: true,
  // Vazio de proposito: em producao o Angular e a API sao servidos pela mesma
  // origem, com o nginx fazendo proxy de /auth e /missions para o backend.
  // Assim a imagem nao carrega host fixo e roda em qualquer EC2 ou dominio,
  // sem rebuild e sem precisar de CORS.
  apiUrl: ''
};
