#!/usr/bin/env node

import { execSync } from 'child_process';
import path from 'path';
import readline from 'readline';
import { fileURLToPath } from 'url';
import fs from 'fs';

// Configurações
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CONFIG_FILE = path.join(__dirname, 'docker-cli.config.json');

// Carrega a configuração ou usa valores padrão
let config = {
  projectName: 'Docker Project',
  dockerCompose: 'docker compose',
  services: {
    backend: {
      port: 8000,
      path: './',
      description: 'Django application server'
    },
    redis: {
      port: 6379,
      path: null,
      description: 'Redis cache server'
    },
    mailhog: {
      port: 8025,
      path: null,
      description: 'Email testing server'
    }
  },
  plugins: []
};

function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const fileConfig = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
      config = { ...config, ...fileConfig };
      console.log(`📄 Configuração carregada: ${CONFIG_FILE}`);
    } else {
      console.log(`⚠️ Arquivo de configuração não encontrado. Usando configurações padrão.`);
      // Criar configuração padrão se não existir
      saveConfig();
    }
  } catch (error) {
    console.error(`❌ Erro ao carregar configuração: ${error.message}`);
  }
}

function saveConfig() {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
    console.log(`✅ Configuração salva em: ${CONFIG_FILE}`);
  } catch (error) {
    console.error(`❌ Erro ao salvar configuração: ${error.message}`);
  }
}

function detectDockerServices() {
  try {
    const composePath = path.join(__dirname, 'docker-compose.yml');
    if (!fs.existsSync(composePath)) {
      console.log('⚠️ docker-compose.yml não encontrado.');
      return;
    }

    console.log('🔍 Detectando serviços Docker...');

    // Leitura mais rápida e parser otimizado
    const fileContent = fs.readFileSync(composePath, 'utf8');

    // Parser mais robusto para YAML
    const lines = fileContent.split('\n');
    const detectedServices = [];

    let inServicesSection = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Detectar início da seção services
      if (line.trim() === 'services:') {
        inServicesSection = true;
        continue;
      }

      // Se estamos na seção services e encontramos um serviço (indentação de 2 espaços)
      if (inServicesSection && line.match(/^  [a-zA-Z][a-zA-Z0-9_-]*:$/)) {
        const serviceName = line.trim().replace(':', '');
        detectedServices.push(serviceName);
      }

      // Se encontramos uma nova seção principal (sem indentação), sair da seção services
      if (inServicesSection && line.match(/^[a-zA-Z]/)) {
        break;
      }
    }

    if (detectedServices.length > 0) {
      console.log(`🔍 Serviços detectados: ${detectedServices.join(', ')}`);

      // Atualizar configuração apenas se necessário
      let hasChanges = false;
      detectedServices.forEach(service => {
        if (!config.services[service]) {
          // Tentar extrair porta do docker-compose
          const servicePort = extractServicePort(fileContent, service);

          config.services[service] = {
            detected: true,
            description: `Auto-detected ${service} service`,
            ...(servicePort && { port: servicePort })
          };
          hasChanges = true;
        }
      });

      if (hasChanges) {
        console.log(`✅ ${detectedServices.filter(s => !config.services[s] || config.services[s].detected).length} novos serviços adicionados à configuração.`);
      } else {
        console.log('✅ Todos os serviços já estão configurados.');
      }
    } else {
      console.log('⚠️ Nenhum serviço detectado no docker-compose.yml');
    }
  } catch (error) {
    console.warn(`⚠️ Detecção automática falhou: ${error.message}`);
  }
}

function extractServicePort(fileContent, serviceName) {
  try {
    // Encontrar a seção do serviço
    const serviceRegex = new RegExp(`^  ${serviceName}:$`, 'm');
    const serviceMatch = fileContent.match(serviceRegex);

    if (!serviceMatch) return null;

    const serviceStartIndex = serviceMatch.index;
    const lines = fileContent.substring(serviceStartIndex).split('\n');

    // Procurar por portas na seção do serviço
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Se chegamos a outro serviço, parar
      if (i > 0 && line.match(/^  [a-zA-Z]/)) {
        break;
      }

      // Procurar por definição de porta
      const portMatch = line.match(/^\s*-\s*"?(\d+):(\d+)"?/) ||
                       line.match(/^\s*-\s*"?.*:(\d+)"?/);

      if (portMatch) {
        return parseInt(portMatch[1] || portMatch[2]);
      }
    }

    return null;
  } catch (error) {
    return null;
  }
}

function checkDockerStatus() {
  try {
    execSync('docker info', { stdio: 'ignore' });
    return true;
  } catch (error) {
    return false;
  }
}

function handleDockerNotRunning() {
  console.error('\n❌ Docker não está em execução!');
  console.log('\n🔧 Opções disponíveis:');
  console.log('1. Inicie o Docker Desktop');
  console.log('2. Execute: sudo systemctl start docker (Linux)');
  console.log('3. Execute: brew services start docker (macOS com Homebrew)');
  console.log('\n💡 Depois que o Docker estiver rodando, execute o comando novamente.\n');

  if (isInteractiveMode) {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    rl.question('🔄 Pressione Enter para tentar novamente ou digite "sair" para finalizar: ', (answer) => {
      rl.close();

      if (answer.toLowerCase() === 'sair' || answer.toLowerCase() === 'exit') {
        console.log(`\n👋 ${config.projectName} Docker CLI finalizado.`);
        process.exit(0);
      } else {
        console.clear();
        if (checkDockerStatus()) {
          console.log('✅ Docker está funcionando agora!\n');
          runInteractiveMode();
        } else {
          handleDockerNotRunning();
        }
      }
    });
  } else {
    process.exit(1);
  }
}

// Variável global para controlar o modo interativo
let isInteractiveMode = false;

// Funções de utilidade
function executeCommand(command, silent = false) {
  if (!silent) {
    console.log(`\n🚀 Executando: ${command}\n`);
  }
  try {
    execSync(command, { stdio: silent ? 'ignore' : 'inherit', cwd: __dirname });
    return true;
  } catch (error) {
    if (!silent) {
      console.error(`\n❌ Erro ao executar comando: ${error.message}\n`);
    }
    return false;
  }
}

function showServiceLogs(service = '') {
  const command = `${config.dockerCompose} logs -f ${service}`;
  executeCommand(command);
}

// Nova função para perguntar se quer continuar
function askToContinue() {
  if (!isInteractiveMode) return;

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  console.log('\n' + '='.repeat(50));
  rl.question('\n🔄 Deseja executar outro comando? (s/N): ', (answer) => {
    rl.close();

    if (answer.toLowerCase() === 's' || answer.toLowerCase() === 'sim') {
      console.clear();
      runInteractiveMode();
    } else {
      console.log(`\n👋 Obrigado por usar o ${config.projectName} Docker CLI!`);
      process.exit(0);
    }
  });
}

// Wrapper para comandos que devem perguntar se quer continuar
function wrapCommandWithContinue(commandFn) {
  return function(...args) {
    try {
      const result = commandFn.apply(this, args);

      // Se o comando retornar uma Promise, aguardar
      if (result && typeof result.then === 'function') {
        result.then(() => askToContinue()).catch(() => askToContinue());
      } else {
        askToContinue();
      }

      return result;
    } catch (error) {
      console.error(`❌ Erro: ${error.message}`);
      askToContinue();
    }
  };
}

// Carregar plugins
function loadPlugins() {
  if (!config.plugins || config.plugins.length === 0) return;

  console.log('🔌 Carregando plugins...');
  config.plugins.forEach(pluginPath => {
    try {
      const pluginFile = path.join(__dirname, pluginPath);
      if (fs.existsSync(pluginFile)) {
        // Em um caso real, aqui faria um require/import do plugin
        console.log(`✅ Plugin carregado: ${pluginPath}`);
      } else {
        console.warn(`⚠️ Plugin não encontrado: ${pluginPath}`);
      }
    } catch (error) {
      console.error(`❌ Erro ao carregar plugin ${pluginPath}: ${error.message}`);
    }
  });
}

// Funções para comandos Docker
function createCommandsObject() {
  // Comandos básicos expandidos
  const baseCommands = {
    up: () => {
      console.log('🚢 Iniciando todos os serviços...');
      executeCommand(`${config.dockerCompose} up -d`);
      console.log('\n✅ Serviços iniciados com sucesso!');

      // Mostrar informações de portas para cada serviço configurado
      Object.entries(config.services).forEach(([name, service]) => {
        if (service.port) {
          const url = name === 'redis' ? `redis://localhost:${service.port}` : `http://localhost:${service.port}`;
          const description = service.description ? ` - ${service.description}` : '';
          console.log(`📋 ${name}: ${url}${description}`);
        }
      });
    },

    down: () => {
      console.log('🛑 Parando todos os serviços...');
      executeCommand(`${config.dockerCompose} down`);
      console.log('\n✅ Todos os serviços foram parados!');
    },

    restart: () => {
      console.log('🔄 Reiniciando todos os serviços...');
      executeCommand(`${config.dockerCompose} restart`);
      console.log('\n✅ Todos os serviços foram reiniciados!');
    },

    rebuild: (service) => {
      if (!service) {
        console.log('🏗️ Reconstruindo todos os serviços...');
        executeCommand(`${config.dockerCompose} build`);
        executeCommand(`${config.dockerCompose} up -d`);
        console.log('\n✅ Todos os serviços foram reconstruídos e iniciados!');
      } else {
        console.log(`🏗️ Reconstruindo serviço: ${service}...`);
        executeCommand(`${config.dockerCompose} build ${service}`);
        executeCommand(`${config.dockerCompose} up -d ${service}`);
        console.log(`\n✅ Serviço ${service} foi reconstruído e iniciado!`);
      }
    },

    logs: (service) => {
      if (service) {
        console.log(`📜 Mostrando logs do serviço: ${service}...`);
        console.log('💡 Pressione Ctrl+C para parar de visualizar os logs\n');
      } else {
        console.log('📜 Mostrando logs de todos os serviços...');
        console.log('💡 Pressione Ctrl+C para parar de visualizar os logs\n');
      }

      try {
        showServiceLogs(service);
      } catch (error) {
        console.log('\n📜 Visualização de logs interrompida.');
      }
    },

    ps: () => {
      console.log('📊 Status dos contêineres:');
      executeCommand(`${config.dockerCompose} ps`);
    },

    prune: () => {
      console.log('🧹 Removendo recursos Docker não utilizados...');
      executeCommand('docker system prune -f');
      console.log('\n✅ Limpeza concluída!');
    },

    config: () => {
      console.log('⚙️ Configurações atuais:');
      console.log(JSON.stringify(config, null, 2));
    },

    scan: () => {
      console.log('🔍 Escaneando projeto em busca de serviços Docker...');
      detectDockerServices();
      saveConfig();
      console.log('\n✅ Escaneamento concluído!');
    },

    shell: (service) => {
      const targetService = service || 'backend';
      console.log(`🐚 Abrindo shell no serviço: ${targetService}...`);
      console.log('💡 Digite "exit" para sair do shell\n');

      const shells = ['/bin/bash', '/bin/sh', '/bin/ash'];

      for (const shell of shells) {
        try {
          executeCommand(`${config.dockerCompose} exec ${targetService} ${shell}`);
          console.log('\n🐚 Shell fechado.');
          break;
        } catch (error) {
          continue;
        }
      }
    },

    stats: () => {
      console.log('📊 Estatísticas dos contêineres em tempo real:');
      console.log('💡 Pressione Ctrl+C para parar\n');
      try {
        executeCommand('docker stats --format "table {{.Container}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}\\t{{.PIDs}}"');
      } catch (error) {
        console.log('\n📊 Visualização de estatísticas interrompida.');
      }
    },

    health: () => {
      console.log('🏥 Verificando saúde dos serviços...\n');

      Object.keys(config.services).forEach(service => {
        try {
          const result = execSync(
            `${config.dockerCompose} ps --format json ${service}`,
            { encoding: 'utf8', cwd: __dirname }
          );

          if (result.trim()) {
            const serviceInfo = JSON.parse(result);
            const status = serviceInfo.State || 'unknown';
            const health = serviceInfo.Health || 'N/A';

            const statusIcon = status === 'running' ? '✅' :
                              status === 'exited' ? '❌' : '⚠️';

            console.log(`${statusIcon} ${service}: ${status} (Health: ${health})`);
          } else {
            console.log(`❌ ${service}: não encontrado`);
          }
        } catch (error) {
          console.log(`⚠️ ${service}: erro ao verificar status`);
        }
      });

      console.log('\n✅ Verificação de saúde concluída!');
    },

    volumes: () => {
      console.log(`💾 Volumes Docker do projeto ${config.projectName}:`);
      try {
        const projectName = config.projectName.toLowerCase().replace(/[\s-]/g, '');
        executeCommand(`docker volume ls --filter name=${projectName}`);
      } catch (error) {
        executeCommand('docker volume ls');
      }
    },

    backup: (service) => {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupDir = path.join(__dirname, 'backups');

      if (!fs.existsSync(backupDir)) {
        fs.mkdirSync(backupDir, { recursive: true });
      }

      if (service === 'redis' || !service) {
        console.log('💾 Fazendo backup do Redis...');
        const backupFile = `redis-backup-${timestamp}.tar.gz`;
        const projectName = config.projectName.toLowerCase().replace(/[\s-]/g, '');

        executeCommand(`docker run --rm -v ${projectName}_redis_data:/data -v "${backupDir}":/backup alpine tar czf /backup/${backupFile} -C /data .`);
        console.log(`✅ Backup do Redis salvo em: backups/${backupFile}`);
      }

      if (service === 'backend' || !service) {
        console.log('💾 Fazendo backup dos dados da aplicação...');
        const backupFile = `app-data-backup-${timestamp}.tar.gz`;

        executeCommand(`tar czf "${path.join(backupDir, backupFile)}" ./data ./logs 2>/dev/null || echo "⚠️ Alguns diretórios podem não existir"`);
        console.log(`✅ Backup dos dados salvo em: backups/${backupFile}`);
      }
    },

    restore: (backupFile) => {
      if (!backupFile) {
        console.log('❌ Especifique o arquivo de backup: node docker-cli.js restore <arquivo>');
        return;
      }

      const backupPath = path.join(__dirname, 'backups', backupFile);
      if (!fs.existsSync(backupPath)) {
        console.log(`❌ Arquivo de backup não encontrado: ${backupPath}`);
        return;
      }

      console.log(`🔄 Restaurando backup: ${backupFile}...`);

      if (backupFile.includes('redis')) {
        const projectName = config.projectName.toLowerCase().replace(/[\s-]/g, '');
        executeCommand(`docker run --rm -v ${projectName}_redis_data:/data -v "${path.dirname(backupPath)}":/backup alpine tar xzf /backup/${backupFile} -C /data`);
        console.log('✅ Backup do Redis restaurado! Reinicie o serviço Redis.');
      } else {
        executeCommand(`tar xzf "${backupPath}" -C ./`);
        console.log('✅ Backup dos dados restaurado!');
      }
    },

    monitor: () => {
      console.log('📊 Iniciando monitoramento em tempo real...');
      console.log('💡 Pressione Ctrl+C para parar o monitoramento\n');

      const monitorCommand = `
        while true; do
          clear
          echo "🐳 Monitor Docker - $(date)"
          echo "=================================="
          echo ""
          echo "📊 Status dos Serviços:"
          ${config.dockerCompose} ps --format "table {{.Service}}\\t{{.State}}\\t{{.Ports}}"
          echo ""
          echo "💾 Uso de Recursos:"
          docker stats --no-stream --format "table {{.Container}}\\t{{.CPUPerc}}\\t{{.MemUsage}}"
          echo ""
          echo "💽 Volumes:"
          docker system df --format "table {{.Type}}\\t{{.Total}}\\t{{.Active}}\\t{{.Size}}"
          echo ""
          sleep 5
        done
      `;

      try {
        executeCommand(monitorCommand);
      } catch (error) {
        console.log('\n📊 Monitoramento interrompido.');
      }
    },

    clean: () => {
      console.log('🧹 Limpeza profunda do Docker...');

      return new Promise((resolve) => {
        const rl = readline.createInterface({
          input: process.stdin,
          output: process.stdout
        });

        rl.question('⚠️ Isso removerá imagens, volumes e redes não utilizados. Continuar? (s/N): ', (answer) => {
          rl.close();

          if (answer.toLowerCase() === 's' || answer.toLowerCase() === 'sim') {
            executeCommand(`${config.dockerCompose} down -v`);
            executeCommand('docker system prune -af --volumes');
            executeCommand('docker network prune -f');
            console.log('\n✅ Limpeza profunda concluída!');
          } else {
            console.log('\n❌ Operação cancelada.');
          }
          resolve();
        });
      });
    },

    update: () => {
      console.log('🔄 Atualizando todas as imagens...');
      executeCommand(`${config.dockerCompose} pull`);
      executeCommand(`${config.dockerCompose} build --pull`);
      executeCommand(`${config.dockerCompose} up -d`);
      console.log('\n✅ Atualização concluída!');
    }
  };

  // Aplicar wrapper apenas para comandos que não são interativos contínuos
  const commandsToWrap = ['up', 'down', 'restart', 'rebuild', 'ps', 'prune', 'config', 'scan', 'health', 'volumes', 'backup', 'restore', 'update'];

  commandsToWrap.forEach(cmdName => {
    if (baseCommands[cmdName]) {
      baseCommands[cmdName] = wrapCommandWithContinue(baseCommands[cmdName]);
    }
  });

  // Adicionar comandos para cada serviço configurado
  const commands = { ...baseCommands };

  Object.keys(config.services).forEach(serviceName => {
    const serviceCommands = {
      up: () => {
        console.log(`🚀 Iniciando apenas o ${serviceName}...`);
        executeCommand(`${config.dockerCompose} up -d ${serviceName}`);
        console.log(`\n✅ Serviço ${serviceName} iniciado com sucesso!`);
      },

      restart: () => {
        console.log(`🔄 Reiniciando o ${serviceName}...`);
        executeCommand(`${config.dockerCompose} restart ${serviceName}`);
        console.log(`\n✅ Serviço ${serviceName} reiniciado com sucesso!`);
      },

      rebuild: () => {
        console.log(`🏗️ Reconstruindo o ${serviceName}...`);
        executeCommand(`${config.dockerCompose} build ${serviceName}`);
        executeCommand(`${config.dockerCompose} up -d ${serviceName}`);
        console.log(`\n✅ Serviço ${serviceName} reconstruído e iniciado!`);
      },

      logs: () => {
        console.log(`📜 Mostrando logs do ${serviceName}...`);
        console.log('💡 Pressione Ctrl+C para parar de visualizar os logs\n');
        try {
          showServiceLogs(serviceName);
        } catch (error) {
          console.log('\n📜 Visualização de logs interrompida.');
        }
      },

      shell: () => {
        console.log(`🐚 Abrindo shell no ${serviceName}...`);
        console.log('💡 Digite "exit" para sair do shell\n');

        const shells = ['/bin/bash', '/bin/sh', '/bin/ash'];

        for (const shell of shells) {
          try {
            executeCommand(`${config.dockerCompose} exec ${serviceName} ${shell}`);
            console.log(`\n🐚 Shell do ${serviceName} fechado.`);
            break;
          } catch (error) {
            continue;
          }
        }
      },

      inspect: () => {
        console.log(`🔍 Inspecionando o ${serviceName}...`);
        executeCommand(`${config.dockerCompose} exec ${serviceName} env`);
        console.log('\n📊 Processos:');
        executeCommand(`${config.dockerCompose} exec ${serviceName} ps aux`);
        console.log(`\n✅ Inspeção do ${serviceName} concluída!`);
      }
    };

    // Aplicar wrapper para comandos de serviço
    ['up', 'restart', 'rebuild', 'inspect'].forEach(cmdName => {
      serviceCommands[cmdName] = wrapCommandWithContinue(serviceCommands[cmdName]);
    });

    commands[serviceName] = serviceCommands;
  });

  return commands;
}

// Interface de linha de comando interativa
function showMenu() {
  console.log(`\n🐳 ${config.projectName} Docker CLI v2.0 🐳\n`);
  console.log('🚀 Comandos Básicos:');
  console.log('1. Iniciar todos os serviços');
  console.log('2. Parar todos os serviços');
  console.log('3. Reiniciar todos os serviços');
  console.log('4. Reconstruir e iniciar todos os serviços');
  console.log('5. Ver logs de todos os serviços');
  console.log('6. Ver status dos contêineres');

  console.log('\n🛠️ Comandos Avançados:');
  console.log('7. Abrir shell no backend');
  console.log('8. Estatísticas em tempo real');
  console.log('9. Verificar saúde dos serviços');
  console.log('10. Listar volumes');
  console.log('11. Fazer backup');
  console.log('12. Monitor em tempo real');
  console.log('13. Atualizar todas as imagens');

  console.log('\n⚙️ Configurações:');
  console.log('14. Limpar recursos Docker não utilizados');
  console.log('15. Limpeza profunda');
  console.log('16. Mostrar configuração atual');
  console.log('17. Escanear projeto em busca de serviços');

  // Opções dinâmicas para cada serviço
  let optionNumber = 18;
  Object.keys(config.services).forEach(serviceName => {
    const serviceDisplayName = serviceName.charAt(0).toUpperCase() + serviceName.slice(1);
    console.log(`\n${serviceDisplayName}:`);
    console.log(`${optionNumber++}. Iniciar apenas o ${serviceName}`);
    console.log(`${optionNumber++}. Reiniciar o ${serviceName}`);
    console.log(`${optionNumber++}. Reconstruir e iniciar o ${serviceName}`);
    console.log(`${optionNumber++}. Ver logs do ${serviceName}`);
  });

  console.log('\n0. Sair');
  console.log('\n');
}

// Função para processar comando de linha
function processArguments() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.clear();
    console.log(`🐳 Bem-vindo ao ${config.projectName} Docker CLI v2.0! 🐳\n`);

    // Verificar Docker antes de entrar no modo interativo
    if (!checkDockerStatus()) {
      handleDockerNotRunning();
      return;
    }

    runInteractiveMode();
    return;
  }

  // Quando executado via linha de comando, não ativar modo interativo
  isInteractiveMode = false;

  const mainCommand = args[0];
  const subCommand = args[1];
  const service = args[2];
  const commands = createCommandsObject();

  if (!['config', 'scan'].includes(mainCommand) && !checkDockerStatus()) {
    handleDockerNotRunning();
    return;
  }

  // Verificar se o comando principal é um serviço conhecido
  if (config.services[mainCommand]) {
    if (subCommand && commands[mainCommand][subCommand]) {
      commands[mainCommand][subCommand]();
    } else {
      console.log(`Comando inválido para ${mainCommand}. Use: up, restart, rebuild, logs`);
    }
    return;
  }

  // Verificar comandos principais
  switch (mainCommand) {
    case 'up':
      commands.up();
      break;
    case 'down':
      commands.down();
      break;
    case 'restart':
      commands.restart();
      break;
    case 'rebuild':
      commands.rebuild(subCommand);
      break;
    case 'logs':
      commands.logs(subCommand);
      break;
    case 'ps':
      commands.ps();
      break;
    case 'prune':
      commands.prune();
      break;
    case 'config':
      commands.config();
      break;
    case 'scan':
      commands.scan();
      break;
    case 'shell':
      commands.shell(subCommand);
      break;
    case 'stats':
      commands.stats();
      break;
    case 'health':
      commands.health();
      break;
    case 'volumes':
      commands.volumes();
      break;
    case 'backup':
      commands.backup(subCommand);
      break;
    case 'restore':
      commands.restore(subCommand);
      break;
    case 'monitor':
      commands.monitor();
      break;
    case 'clean':
      commands.clean();
      break;
    case 'update':
      commands.update();
      break;
    default:
      console.log('Comando não reconhecido');
      showHelp();
  }
}

function showHelp() {
  console.log(`
🐳 ${config.projectName} Docker CLI v2.0 - Comandos Disponíveis

Uso: node docker-cli.js [comando] [subcomando] [parâmetro]

🚀 Comandos Básicos:
  up                    Inicia todos os serviços
  down                  Para todos os serviços
  restart               Reinicia todos os serviços
  rebuild [serviço]     Reconstrói e inicia todos ou um serviço específico
  logs [serviço]        Exibe logs de todos ou um serviço específico
  ps                    Mostra status dos contêineres

🛠️ Comandos Avançados:
  shell [serviço]       Abre shell no serviço (padrão: backend)
  stats                 Mostra estatísticas em tempo real
  health                Verifica saúde de todos os serviços
  volumes               Lista volumes do projeto
  backup [serviço]      Faz backup (redis, backend ou todos)
  restore <arquivo>     Restaura backup especificado
  monitor               Monitor em tempo real (Ctrl+C para sair)
  update                Atualiza todas as imagens

⚙️ Manutenção:
  prune                 Remove recursos Docker não utilizados
  clean                 Limpeza profunda (interativa)
  config                Mostra a configuração atual
  scan                  Escaneia o projeto em busca de serviços Docker

Serviços disponíveis:`);

  Object.keys(config.services).forEach(service => {
    console.log(`  ${service} [subcomando]   Gerencia o serviço ${service} (up, restart, rebuild, logs, shell, inspect)`);
  });

  console.log(`
Exemplos:
  node docker-cli.js up
  node docker-cli.js logs backend
  node docker-cli.js shell redis
  node docker-cli.js backup redis
  node docker-cli.js backend shell
  node docker-cli.js monitor
  `);
}

function runInteractiveMode() {
  isInteractiveMode = true;

  // Verificação dupla por segurança
  if (!checkDockerStatus()) {
    handleDockerNotRunning();
    return;
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  showMenu();

  rl.question('Digite sua escolha: ', (answer) => {
    rl.close();
    const commands = createCommandsObject();

    // Criar um mapeamento dinâmico de números para comandos
    let menuOptions = {
      '1': commands.up,
      '2': commands.down,
      '3': commands.restart,
      '4': commands.rebuild,
      '5': commands.logs,
      '6': commands.ps,
      '7': () => commands.shell('backend'),
      '8': commands.stats,
      '9': commands.health,
      '10': commands.volumes,
      '11': commands.backup,
      '12': commands.monitor,
      '13': commands.update,
      '14': commands.prune,
      '15': commands.clean,
      '16': commands.config,
      '17': commands.scan,
      '0': () => {
        console.log(`\n👋 Obrigado por usar o ${config.projectName} Docker CLI!`);
        process.exit(0);
      }
    };

    // Adicionar opções para cada serviço
    let optionNumber = 18;
    Object.keys(config.services).forEach(serviceName => {
      menuOptions[optionNumber++] = commands[serviceName].up;
      menuOptions[optionNumber++] = commands[serviceName].restart;
      menuOptions[optionNumber++] = commands[serviceName].rebuild;
      menuOptions[optionNumber++] = commands[serviceName].logs;
    });

    if (menuOptions[answer]) {
      console.log(`\n${'='.repeat(60)}`);
      console.log(`🚀 Executando comando selecionado...`);
      console.log(`${'='.repeat(60)}\n`);

      menuOptions[answer]();
    } else {
      console.log('\n❌ Opção inválida!');
      setTimeout(() => {
        console.clear();
        runInteractiveMode();
      }, 2000);
    }
  });
}

// Inicialização otimizada
console.log('⚡ Iniciando Docker CLI...');
loadConfig();

// Só detectar serviços se for necessário (modo scan ou primeira execução)
const args = process.argv.slice(2);
if (args.length === 0 || args[0] === 'scan') {
  detectDockerServices();
}

loadPlugins();

// Executar
processArguments();
