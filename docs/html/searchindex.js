Search.setIndex({docnames:["audio","bots","commands","database","error","index","network","utils"],envversion:{"sphinx.domains.c":1,"sphinx.domains.changeset":1,"sphinx.domains.cpp":1,"sphinx.domains.javascript":1,"sphinx.domains.math":2,"sphinx.domains.python":1,"sphinx.domains.rst":1,"sphinx.domains.std":1,"sphinx.ext.intersphinx":1,sphinx:56},filenames:["audio.rst","bots.rst","commands.rst","database.rst","error.rst","index.rst","network.rst","utils.rst"],objects:{"royalnet.audio":{PlayMode:[0,1,1,""],Playlist:[0,1,1,""],Pool:[0,1,1,""],RoyalPCMAudio:[0,1,1,""],RoyalPCMFile:[0,1,1,""],YtdlFile:[0,1,1,""],YtdlInfo:[0,1,1,""]},"royalnet.audio.PlayMode":{"delete":[0,2,1,""],__init__:[0,2,1,""],_generate_generator:[0,2,1,""],add:[0,2,1,""],next:[0,2,1,""],videos_left:[0,2,1,""]},"royalnet.audio.Playlist":{"delete":[0,2,1,""],__init__:[0,2,1,""],_generate_generator:[0,2,1,""],add:[0,2,1,""],videos_left:[0,2,1,""]},"royalnet.audio.Pool":{"delete":[0,2,1,""],__init__:[0,2,1,""],_generate_generator:[0,2,1,""],add:[0,2,1,""],videos_left:[0,2,1,""]},"royalnet.audio.RoyalPCMAudio":{"delete":[0,2,1,""],__init__:[0,2,1,""],create_from_url:[0,3,1,""],create_from_ytsearch:[0,3,1,""],is_opus:[0,2,1,""],read:[0,2,1,""]},"royalnet.audio.RoyalPCMFile":{audio_filename:[0,4,1,""],create_from_url:[0,3,1,""],create_from_ytsearch:[0,3,1,""],delete_audio_file:[0,2,1,""],ytdl_args:[0,4,1,""],ytdl_filename:[0,4,1,""]},"royalnet.audio.YtdlFile":{_stop_download:[0,2,1,""],create_from_url:[0,3,1,""],delete_video_file:[0,2,1,""],ytdl_args:[0,4,1,""]},"royalnet.audio.YtdlInfo":{__init__:[0,2,1,""],create_from_url:[0,3,1,""],download:[0,2,1,""]},"royalnet.bots":{DiscordBot:[1,1,1,""],DiscordConfig:[1,1,1,""],GenericBot:[1,1,1,""],TelegramBot:[1,1,1,""],TelegramConfig:[1,1,1,""]},"royalnet.bots.DiscordBot":{_bot_factory:[1,2,1,""],_call_factory:[1,2,1,""],_init_client:[1,2,1,""],_init_voice:[1,2,1,""],add_to_music_data:[1,2,1,""],advance_music_data:[1,2,1,""],interface_name:[1,4,1,""],run:[1,2,1,""],update_activity_with_source_title:[1,2,1,""]},"royalnet.bots.GenericBot":{_call_factory:[1,2,1,""],_init_commands:[1,2,1,""],_init_database:[1,2,1,""],_init_royalnet:[1,2,1,""],_network_handler:[1,2,1,""],call:[1,2,1,""],interface_name:[1,4,1,""],run:[1,2,1,""]},"royalnet.bots.TelegramBot":{_call_factory:[1,2,1,""],_handle_update:[1,2,1,""],_init_client:[1,2,1,""],botfather_command_string:[1,4,1,""],interface_name:[1,4,1,""],run:[1,2,1,""]},"royalnet.commands":{AuthorCommand:[2,1,1,""],CiaoruoziCommand:[2,1,1,""],ColorCommand:[2,1,1,""],CvCommand:[2,1,1,""],DateparserCommand:[2,1,1,""],DiarioCommand:[2,1,1,""],KvCommand:[2,1,1,""],KvactiveCommand:[2,1,1,""],KvrollCommand:[2,1,1,""],MissingCommand:[2,1,1,""],NullCommand:[2,1,1,""],PingCommand:[2,1,1,""],PlayCommand:[2,1,1,""],PlaymodeCommand:[2,1,1,""],RageCommand:[2,1,1,""],ReminderCommand:[2,1,1,""],ShipCommand:[2,1,1,""],SkipCommand:[2,1,1,""],SmecdsCommand:[2,1,1,""],SummonCommand:[2,1,1,""],SyncCommand:[2,1,1,""],VideochannelCommand:[2,1,1,""],VideoinfoCommand:[2,1,1,""]},"royalnet.database":{Alchemy:[3,1,1,""],DatabaseConfig:[3,1,1,""],relationshiplinkchain:[3,5,1,""],tables:[3,0,0,"-"]},"royalnet.database.Alchemy":{__init__:[3,2,1,""],_create_tables:[3,2,1,""],session_acm:[3,2,1,""],session_cm:[3,2,1,""]},"royalnet.database.tables":{ActiveKvGroup:[3,1,1,""],Alias:[3,1,1,""],Diario:[3,1,1,""],Discord:[3,1,1,""],Keygroup:[3,1,1,""],Keyvalue:[3,1,1,""],Royal:[3,1,1,""],Telegram:[3,1,1,""]},"royalnet.database.tables.ActiveKvGroup":{group:[3,4,1,""],group_name:[3,4,1,""],royal:[3,4,1,""],royal_id:[3,4,1,""]},"royalnet.database.tables.Alias":{alias:[3,4,1,""],royal:[3,4,1,""],royal_id:[3,4,1,""]},"royalnet.database.tables.Diario":{context:[3,4,1,""],creator:[3,4,1,""],creator_id:[3,4,1,""],diario_id:[3,4,1,""],media_url:[3,4,1,""],quoted:[3,4,1,""],quoted_account:[3,4,1,""],quoted_account_id:[3,4,1,""],spoiler:[3,4,1,""],text:[3,4,1,""],timestamp:[3,4,1,""]},"royalnet.database.tables.Discord":{avatar_hash:[3,4,1,""],discord_id:[3,4,1,""],discriminator:[3,4,1,""],full_username:[3,2,1,""],royal:[3,4,1,""],royal_id:[3,4,1,""],username:[3,4,1,""]},"royalnet.database.tables.Keygroup":{group_name:[3,4,1,""]},"royalnet.database.tables.Keyvalue":{group:[3,4,1,""],group_name:[3,4,1,""],key:[3,4,1,""],value:[3,4,1,""]},"royalnet.database.tables.Royal":{avatar:[3,4,1,""],password:[3,4,1,""],role:[3,4,1,""],uid:[3,4,1,""],username:[3,4,1,""]},"royalnet.database.tables.Telegram":{first_name:[3,4,1,""],last_name:[3,4,1,""],mention:[3,2,1,""],royal:[3,4,1,""],royal_id:[3,4,1,""],tg_id:[3,4,1,""],username:[3,4,1,""]},"royalnet.error":{ExternalError:[4,6,1,""],InvalidConfigError:[4,6,1,""],InvalidInputError:[4,6,1,""],NoneFoundError:[4,6,1,""],RoyalnetRequestError:[4,6,1,""],RoyalnetResponseError:[4,6,1,""],TooManyFoundError:[4,6,1,""],UnregisteredError:[4,6,1,""],UnsupportedError:[4,6,1,""]},"royalnet.network":{ConnectionClosedError:[6,6,1,""],NetworkError:[6,6,1,""],NotConnectedError:[6,6,1,""],NotIdentifiedError:[6,6,1,""],Package:[6,1,1,""],Request:[6,1,1,""],Response:[6,1,1,""],ResponseError:[6,1,1,""],ResponseSuccess:[6,1,1,""],RoyalnetConfig:[6,1,1,""],RoyalnetLink:[6,1,1,""],RoyalnetServer:[6,1,1,""]},"royalnet.network.Package":{__init__:[6,2,1,""],from_dict:[6,3,1,""],from_json_bytes:[6,3,1,""],from_json_string:[6,3,1,""],reply:[6,2,1,""],to_dict:[6,2,1,""],to_json_bytes:[6,2,1,""],to_json_string:[6,2,1,""]},"royalnet.network.Request":{from_dict:[6,3,1,""],to_dict:[6,2,1,""]},"royalnet.network.Response":{from_dict:[6,7,1,""],raise_on_error:[6,2,1,""],to_dict:[6,2,1,""]},"royalnet.network.ResponseError":{raise_on_error:[6,2,1,""]},"royalnet.network.ResponseSuccess":{raise_on_error:[6,2,1,""]},"royalnet.network.RoyalnetLink":{connect:[6,2,1,""],identify:[6,2,1,""],receive:[6,2,1,""],request:[6,2,1,""],run:[6,2,1,""],send:[6,2,1,""]},"royalnet.network.RoyalnetServer":{find_client:[6,2,1,""],find_destination:[6,2,1,""],listener:[6,2,1,""],route_package:[6,2,1,""],serve:[6,2,1,""],start:[6,2,1,""]},"royalnet.utils":{Call:[7,1,1,""],Command:[7,1,1,""],CommandArgs:[7,1,1,""],NetworkHandler:[7,1,1,""],andformat:[7,5,1,""],asyncify:[7,5,1,""],cdj:[7,5,1,""],fileformat:[7,5,1,""],plusformat:[7,5,1,""],safeformat:[7,5,1,""],sleep_until:[7,5,1,""]},"royalnet.utils.Call":{__init__:[7,2,1,""],_session_init:[7,2,1,""],alchemy:[7,4,1,""],get_author:[7,2,1,""],interface_name:[7,4,1,""],interface_obj:[7,4,1,""],interface_prefix:[7,4,1,""],net_request:[7,2,1,""],reply:[7,2,1,""],run:[7,2,1,""],session_end:[7,2,1,""]},"royalnet.utils.Command":{command_description:[7,4,1,""],command_name:[7,4,1,""],command_syntax:[7,4,1,""],common:[7,7,1,""],network_handler_dict:[7,7,1,""],network_handlers:[7,4,1,""],require_alchemy_tables:[7,4,1,""]},"royalnet.utils.CommandArgs":{__getitem__:[7,2,1,""],joined:[7,2,1,""],match:[7,2,1,""],optional:[7,2,1,""]},"royalnet.utils.NetworkHandler":{message_type:[7,4,1,""]},royalnet:{audio:[0,0,0,"-"],bots:[1,0,0,"-"],commands:[2,0,0,"-"],database:[3,0,0,"-"],error:[4,0,0,"-"],network:[6,0,0,"-"],utils:[7,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","staticmethod","Python static method"],"4":["py","attribute","Python attribute"],"5":["py","function","Python function"],"6":["py","exception","Python exception"],"7":["py","classmethod","Python class method"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:staticmethod","4":"py:attribute","5":"py:function","6":"py:exception","7":"py:classmethod"},terms:{"0x7a5f150":3,"0x7a5f588":3,"0x7a5f738":3,"0x7a5f978":3,"0x7a5fa98":3,"0x7a5fae0":3,"0x7a5fc48":3,"20m":0,"48khz":0,"abstract":7,"boolean":3,"byte":[0,6],"class":[0,1,2,3,6,7],"default":[0,3,7],"final":7,"float":0,"function":[0,4,7],"int":[0,6,7],"new":[0,1,3,7],"null":[1,6],"return":[0,1,4,6,7],"static":[0,6],"true":[0,3,7],"try":[1,7],"while":[0,1,3,4,7],Not:0,That:7,The:[0,1,3,4,6,7],Then:1,These:2,Use:3,__dict__:7,__doc__:7,__getitem__:7,__init__:[0,3,6,7],__module__:7,__weakref__:7,_bot_factori:1,_call_factori:1,_create_t:3,_generate_gener:0,_handle_upd:1,_init_cli:1,_init_command:1,_init_databas:1,_init_royalnet:1,_init_voic:1,_network_handl:1,_session_init:7,_stop_download:0,_windowsselectoreventloop:6,abl:7,about:[0,6],abstracteventloop:6,access:7,accur:7,activekvgroup:3,add:[0,1],add_to_music_data:1,added:7,adding:7,addit:[6,7],address:6,advanc:0,advance_music_data:1,akin:6,alchemi:[1,3,7],alia:3,all:[0,6,7],allow:3,alreadi:0,also:[0,6],altern:6,alwai:1,amount:[0,7],andformat:7,ani:[0,7],anoth:[1,6],anymor:6,anystr:7,arg:[6,7],argument:[0,7],around:[0,3],arrai:7,async:[0,3],asyncifi:7,asyncio:[1,6],asyncron:3,attempt:7,attribut:7,audio:[1,5],audio_filenam:0,audio_sourc:1,audiosourc:0,author:7,authorcommand:2,avatar:3,avatar_hash:3,base:[0,1,6,7],been:[0,4],being:4,bestaudio:0,between:7,biginteg:3,bit:0,block:[1,7],blockingli:6,bot:[0,2,3,4,5,7],botfather_command_str:1,both:3,call:[1,7],callabl:7,can:[2,4,6,7],cancel:7,cannot:[4,7],cdj:7,chain:1,chang:[0,1],change_pres:1,channel:[1,7],charact:7,chat:1,check:[0,2,3],ciaoruozicommand:2,class_:7,classmethod:[6,7],client:1,close:[6,7],colorcommand:2,column:3,columndefault:3,command:[1,4,5,7],command_arg:7,command_descript:7,command_nam:[1,7],command_prefix:1,command_syntax:7,commandarg:7,common:7,commun:[2,6],compat:0,complet:[0,4],compon:[3,4],configur:[1,3,4],connect:[1,6],connectedcli:6,connectionclosederror:6,contain:[0,4,6],context:3,convers:6,convert:[0,6,7],core:3,coroutin:[1,7],correctli:4,correspond:[0,1],creat:[0,1,3,6,7],create_from_url:0,create_from_ytsearch:0,creator:3,creator_id:3,ct_co:3,current:1,custom:[0,1],cvcommand:2,data:[0,6,7],databas:[1,5,7],database_config:1,database_uri:3,databaseconfig:[1,3],dateparsercommand:2,datetim:[3,7],debug:6,declar:[3,7],delet:0,delete_audio_fil:0,delete_video_fil:0,describ:3,descript:6,destin:[6,7],destination_conv_id:6,detail:3,diario:3,diario_id:3,diariocommand:2,dict:[0,1,6,7],dictionari:[1,6],discord:[0,1,3],discord_config:1,discord_id:3,discordbot:1,discordcli:1,discordconfig:1,discrimin:3,doc:3,doe:0,doesn:1,don:7,download:0,dure:1,dynam:7,each:0,either:[0,7],element:[4,7],empti:[0,1],encod:[0,6],end:3,ending_class:3,engin:3,ensur:7,error:[5,6,7],error_command:1,error_data:6,error_if_non:7,event:6,everi:[0,6],except:[1,4,6],execut:[1,4,6,7],exist:1,expect:4,ext:0,externalerror:4,extra:0,extra_info:6,extract:0,extract_info:0,factori:0,fals:[0,3,6,7],file:[0,1],fileformat:7,filenam:7,find:[1,3,6,7],find_client:6,find_destin:6,first:0,first_nam:3,follow:3,foreignkei:3,format:[0,1,7],found:[4,7],frame:0,from:[0,1,3,6,7],from_dict:6,from_json_byt:6,from_json_str:6,full_usernam:3,fullfil:7,game:2,gener:[0,1,7],genericbot:[1,3],get:[0,3,7],get_author:7,going:0,greater:7,group:[3,7],group_nam:3,guild:1,handl:[1,4],handler:6,has:[0,4,6,7],have:1,html:3,http:3,identifi:[6,7],identity_column_nam:3,identity_t:[1,3],ignor:7,implement:0,incom:1,index:[5,7],inf:[0,6],infinit:0,info:[0,6],inherit:[0,1,6],initi:[0,1],input:[4,7],insid:0,instanc:1,instead:[0,7],integ:3,interfac:[1,4],interface_nam:[1,7],interface_obj:7,interface_prefix:7,invalid:[4,6],invalidconfigerror:4,invalidinputerror:[4,7],is_opu:0,item:[0,7],join:7,json:6,jsonabl:6,just:1,keep:0,kei:[3,7],keygroup:3,keyvalu:3,keyword:7,kvactivecommand:2,kvcommand:2,kvrollcommand:2,kwarg:[1,7],largebinari:3,last:7,last_nam:3,least:0,left:0,like:0,link:[1,4,6],link_typ:6,list:[0,1,6,7],listen:[1,6],logger:0,login:1,look:4,loop:6,made:7,mai:[0,7],mainli:0,maintain:3,make:1,manag:3,markup:7,master_secret:6,master_t:[1,3],master_uri:6,match:[1,4,7],math:0,mean:7,media_url:3,memori:0,mention:3,messag:[1,6,7],message_typ:7,method:[0,3],middl:7,minimum:7,miscellan:7,miss:7,missing_command:1,missingcommand:2,modul:5,more:[1,3],multipl:[1,3,4],music_data:1,must:[0,6,7],name:[0,1,6],need:[1,2],net_request:7,network:[1,4,5,7],network_handl:[1,7],network_handler_dict:7,networkerror:6,networkhandl:7,next:[0,1],nid:6,no_warn:0,nobodi:6,node:6,non:[4,7],none:[0,1,3,6,7],nonefounderror:4,noplaylist:0,notat:7,notconnectederror:6,noth:[6,7],notidentifiederror:6,notimpl:[1,7],now_plai:0,nullabl:3,nullcommand:[1,2],number:[0,6],object:[0,1,3,7],offset:1,onc:[0,3],one:4,ones:1,onli:[4,7],option:[0,1,3,6,7],opu:0,order:0,org:3,other:[1,4,6,7],otherwis:[0,1,6,7],output:7,outtmpl:0,packag:6,packet:6,page:5,paramet:[0,1,3,6,7],pass:[0,7],password:3,path:[3,6],pattern:7,pcm:0,per:0,perman:0,pickl:7,pingcommand:2,plai:[0,1],playcommand:2,playlist:0,playmod:0,playmodecommand:2,plusformat:7,pool:0,port:6,possibl:7,prepar:6,presenc:1,previous:7,primary_kei:3,probabl:[0,2,7],properti:0,quiet:0,quot:3,quoted_account:3,quoted_account_id:3,ragecommand:2,rais:[1,4,6,7],raise_on_error:6,random:0,read:0,real:6,realat:6,receiv:[1,4,6,7],reciev:6,recommend:0,recreat:6,refer:2,regex:7,regist:4,relat:[0,3],relationshiplinkchain:3,relationshipproperti:3,remindercommand:2,remov:0,repeat:0,replac:7,repli:[6,7],repres:[0,1],request:[1,4,6],request_dict:1,request_handl:6,requir:[1,4,7],require_alchemy_t:7,require_at_least:7,required_secret:6,respons:[1,4,6],responseerror:[4,6],responsesuccess:6,result:7,retriev:7,role:3,rout:6,route_packag:6,row:7,royal:[2,3],royal_id:3,royalnet_config:1,royalnetconfig:[1,6],royalnetlink:[1,6,7],royalnetrequesterror:4,royalnetresponseerror:4,royalnetserv:6,royalpcmaudio:[0,1],royalpcmfil:0,rpf:0,run:[1,6,7],safeformat:7,search:[0,5],second:7,secret:6,select:[0,3],self:[1,6],send:[6,7],sent:[6,7],sequenc:[6,7],serv:6,server:6,session:7,session_acm:3,session_cm:3,session_end:7,set:[1,3],shipcommand:2,should:[1,6,7],signal:0,singl:[1,3],skipcommand:2,sleep_until:7,smecdscommand:2,someth:[4,7],somewher:6,song:[0,1],soon:0,sourc:[0,6,7],source_conv_id:6,space:7,specif:[1,7],specifi:[1,4,7],spoiler:3,sqlalchemi:[3,7],start:[1,3,6],starting_class:3,starting_list:0,starting_pool:0,statement:3,statu:1,stereo:0,str:[0,1,3,6,7],string:[0,3,6,7],sub:7,subclass:0,submodul:3,success:6,suit:2,summoncommand:2,support:4,synccommand:2,tabl:[1,7],tailor:2,task:1,telegram:[1,3],telegram_config:1,telegrambot:1,telegramcal:1,telegramconfig:1,text:[3,7],tg_id:3,than:7,thei:[2,7],them:[2,3],therefor:4,thi:[0,4,6,7],those:0,through:7,time:6,timestamp:3,titl:0,to_dict:6,to_json_byt:6,to_json_str:6,token:1,toomanyfounderror:4,tupl:3,two:7,type:[0,1,3,6,7],uid:3,underscor:7,undescrib:7,unexpect:7,unexpectedli:6,union:0,univers:7,unregisterederror:[4,7],unsupportederror:4,until:[0,7],updat:1,update_activity_with_source_titl:1,uri:3,url:0,use:[0,3],used:[0,1,2,3,6,7],useful:[0,7],user:[4,7],usernam:3,using:[1,7],usual:[0,6],utf8:6,util:[1,5],valu:[0,3,6,7],variabl:1,variou:1,veri:0,video:0,videochannelcommand:2,videoinfocommand:2,videos_left:0,voic:[0,1],wai:0,wait:7,want:[0,7],warn:0,websocket:6,websocketserverprotocol:6,weird:7,went:4,were:4,when:7,where:7,which:[0,6],without:7,won:2,word:7,worth:0,wrapper:[0,3],wrong:4,yet:6,yield:0,you:[0,2,7],your:2,youtub:0,youtube_dl:0,youtubedl:0,ytdl_arg:0,ytdl_filenam:0,ytdlfile:0,ytdlinfo:0},titles:["royalnet.audio","royalnet.bots","royalnet.commands","royalnet.database","royalnet.error","royalnet","royalnet.network","royalnet.utils"],titleterms:{audio:0,bot:1,command:2,databas:3,error:4,indic:5,network:6,royalnet:[0,1,2,3,4,5,6,7],tabl:[3,5],util:7}})