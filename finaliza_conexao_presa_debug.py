from telnetlib import Telnet
import sys,logging,os,psutil
from imp import reload
diretorio =os.path.dirname(os.path.abspath(sys.argv[0]))

reload(logging)
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename=os.path.join(diretorio,'execucao.log'), filemode='a', level=logging.DEBUG)

# Inicializa listas
par = []
servicos = []


#Efetua a leitura do arquivo de configuração
try:
    
    with open(diretorio+'\config.conf','r') as arq:
        for linha in arq:
            conteudo = linha
            if 'DBCONTROL' in linha:
                conteudo = conteudo.replace('\n','') 
                par.append(conteudo)
            else:
                conteudo = conteudo.replace('\n','')
                servicos.append(conteudo)

#Salva no log se ocorrer algum erro            
except Exception as e:        
    logging.debug(e)
    sys.exit()

#Checa se foi informado os parâmetros necessários para funcionamento do programa
if len(par)+len(servicos) < 2:
    logging.debug('Parâmetros inválidos. Informe conforme o exemplo abaixo: \nDBCONTROL_XXXX_XXX \nServico1\nServico2\nServico3\n...')
    sys.exit()

#Inicializa listas
pid_servicos =[]
processos_vinculados_nssm = []
processos_iscserver = []
processos_java = []
processos_java_pid = []
ip_porta = {}



try:
    
#Busca os servicos com o nome contido no arquivo de configuração e obtém seu PID
    for servico in servicos:
    
        wservice = psutil.win_service_get(servico)
        pid = wservice.pid()
        pid_servicos.append(pid)
        processos_vinculados_nssm.append(psutil.Process(pid).children())

#Obtem os processos vinculados ao serviço do arquivo de configuração cujo nome seja iscserver.exe 
#depois dos processos vinculados ao iscserver.exe
    for processo in processos_vinculados_nssm :
        for linha in processo:
            linha =str(linha)
            if 'iscserver.exe' or 'isserver.exe' in linha:
                linha = linha.split('=')
                linha = str(linha).split(',')
                linha = str(linha[1]).replace ("'","")
                linha = linha.strip()
                x =(psutil.Process(int(linha)).children())
                processos_iscserver.append(linha)
                if x:
                    processos_java.append(x)

#Salva no log se ocorrer algum erro e encerra o programa
except Exception as e:
        logging.debug(e)
        sys.exit()

#Valida se a lista de processos java está vazia

if not processos_java:
    logging.debug('Não foi localizado nenhum PID para ser encerrado.')
    sys.exit()
else:
        
#Filtra os processos vinculados ao iscserver, obtendo somente os que são java.exe

    try:
        if processos_java:
            for processo in processos_java:
            
                for linha in processo:
                    try:
                        linha=str(linha)
                        if 'java.exe' in str(linha):
                            linha = linha.split('=')
                            linha = str(linha).split(',')
                            linha = str(linha[1]).replace ("'","")
                            linha = linha.strip()
                            processos_java_pid.append(linha.strip())
                        
#obtem os dados do processo java.exe, tenta comunicar-se com o ip\porta informado nos dados do 

                            p = psutil.Process(int(linha))
                            p = p.cmdline()
                            comando1 = (p.index('-host'))
                            comando1 +=1
                            ip =p[comando1]
                            comando2 = (p.index('-port'))
                            comando2 +=1
                            porta=int(p[comando2])
                            ip_porta[ip]=porta
                            with Telnet(ip, int(porta)) as tn:
                                tn.interact()
                            

                    except Exception as e:
    
#finaliza o PID caso não consiga se comunicar com o ip\porta

                        if 'WinError 10061' or 'Errno 11001' in str(e) and processos_java_pid:        

                            logging.debug('Finalizado o PID '+linha+' vinculado ao ip e porta '+ip+':'+str(porta))
                        else:
                            logging.debug(e)
                            sys.exit()
    except Exception as e:
       print(e)

