<?php

require '../config.php';
require_once dirname(__DIR__, 3) . '/auth/lib.php';
auth_start_session();
$authId = auth_current_discord_id();
$authName = auth_display_name();
$Session = new \App\Session(); // sux session class and redirect
if($Session->isLogged()==false && $GLOBALS['config']['require_login']==true){
    return header('Location: login.php');
}
?><!DOCTYPE html>
<html lang="es" ng-app="App">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?php echo htmlspecialchars($config['app_name'], ENT_QUOTES, 'UTF-8'); ?></title>
    <link rel="icon" href="/assets/img/favicon.png" type="image/png"/>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.8.3/underscore-min.js"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.5.7/angular.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/angular-sanitize/1.5.7/angular-sanitize.js"></script>
    <script src="js/app.js"></script>
    <script src="js/ApplicationController.js?v=1.2"></script>

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css" integrity="sha384-9aIt2nRpC12Uk9gS9baDl411NQApFmC26EwAOH8WgZl5MYYxFfc+NcPb1dKGj7Sk" crossorigin="anonymous">
	<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">

    <link href="style/template.css" rel="stylesheet">
    <?php /* site.css + logs-theme (despues de Bootstrap para ganar en cascada) */ ?>
    <?php require __DIR__ . '/_latam_chrome.php'; ?>

   <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js" integrity="sha384-OgVRvuATP1z7JjHLkuOU7Xw704+h835Lr+6QL9UvYjZE3Ipu6Tp75j7Bh/kR0JKI" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.24.0/moment-with-locales.min.js"></script>

    <script>
        <?php
        // servers lists
        $servers_list = json_encode($config['servers_list']);
        echo "var server_list = ". $servers_list . ";\n";

        // servers commands
        $server_commands = json_encode($config['server_commands']);
        echo "var server_commands = ". $server_commands . ";\n";
        ?>
    </script>
    <style>
        .tab-block { padding: 10px 0; }
        .divide-col {
            -moz-column-count: 2; -moz-column-gap: 20px;
            -webkit-column-count: 2; -webkit-column-gap: 20px;
            column-count: 2; column-gap: 20px;
        }
        .modal-lg { width: 100%!important; }
        <?php if( !empty($GLOBALS['config']['full_width']) ) { ?>
        .container { width: 98%!important; max-width: 98%!important; }
        <?php } ?>
    </style>
</head>

<body class="logs-body" ng-controller="ApplicationController">
<?php logs_render_latam_header(); ?>

<!-- load contents on angular js -->
<div class="" ng-init="loadContents()">

    <div class="logs-page-title d-flex flex-wrap align-items-baseline justify-content-between">
        <h1 class="m-0"><?php echo htmlspecialchars($config['app_name'], ENT_QUOTES, 'UTF-8'); ?></h1>
        <?php if( !empty($GLOBALS['config']['require_login']) ) { ?>
            <span class="logs-user">
                Hola, <b><?php echo htmlspecialchars(isset($_SESSION['user_name']) ? $_SESSION['user_name'] : '', ENT_QUOTES, 'UTF-8'); ?></b>
                <small><a href="logout.php">Salir</a></small>
            </span>
        <?php } ?>
    </div>

    <div class="container p-4">
    <div class="row">

        <div class="col-md-12">
            <h5 class="mb-3">Elegi el servidor ( {{ selected_server.length }}  <span ng-if="selected_server.length==1">servidor</span> <span ng-if="selected_server.length>=2">servidores</span> seleccionado<span ng-if="selected_server.length!=1">s</span> )</h5>
            <ul class="list-group cursor">
                <li  class="list-group-item py-1"  ng-click="toogleServer(server.id)" ng-class="{'bg-light':inArray(server.id)==true}" ng-repeat="server in server_list">
                    <div class="float-left p-1 font-weight-bold" >
                        {{ server.name }}
                    </div>
                    <button class="btn btn-link  float-right" ng-click="setServer(server);downloadLog(server);toogleServer(server.id)">
                        <div ng-show="server.loading">Cargando</div>
                        <div ng-hide="server.loading">
                            <small><span class="fa fa-refresh"> </span> Actualizado: <span ng-if="!server.timestamp">cargando...</span> {{ server.timestamp }}</small>
                        </div>
                    </button>
                </li>
            </ul>
        </div>

            <div class="col-md-12" ng-hide="selected_server.length==0">
                <div style="height: 17px"></div>
                <!-- tabs -->

                <?php /* PestaÃ±as: misma logica Angular (tab default/player), sin radios */ ?>
                <div class="logs-tabs" role="tablist" aria-label="Tipo de logs">
                    <button
                        type="button"
                        role="tab"
                        class="logs-tabs__btn"
                        ng-class="{'is-active': tab=='default'}"
                        ng-click="tab='default';results=[];results_hash=[]"
                        ng-attr-aria-selected="{{ tab=='default' ? 'true' : 'false' }}"
                    >Logs de admin</button>
                    <button
                        type="button"
                        role="tab"
                        class="logs-tabs__btn"
                        ng-class="{'is-active': tab=='player'}"
                        ng-click="tab='player';results=[];results_hash=[]"
                        ng-attr-aria-selected="{{ tab=='player' ? 'true' : 'false' }}"
                    >Logs de jugadores</button>
                </div>

                <div class="tab-block" ng-show="tab=='default'">
                    <div style="height: 200px; width: 100%; overflow-y: scroll">
                    <ul class="list-group divide-col" >
                        <li  class="list-group-item"   ng-click="setCommand(command.value)" ng-class="{'active':active_command==command.value}" ng-repeat="command in server_commands">
                            <label class="p-0 m-0">
                                {{ command.name }}
                            </label>
                        </li>
                    </ul>
                        <ul class="list-group mt-3" >
                            <li  class="list-group-item"   ng-click="setCommand('ALL')" ng-class="{'active':active_command=='ALL'}">
                                <label>
                                    TODOS LOS COMANDOS POR JUGADOR
                                </label>
                            </li>
                        </ul>
                    </div>


                    <div ng-if="active_command=='ALL'">

                        <div class="input-group input-group-lg">
                            <input type="text" name="search_fall" id="search_fall" class="form-control"  ng-model="search_fall" placeholder="Buscar en todos los datos">
                            <span class="input-group-btn">
                                <button class="btn btn-success btn-lg" ng-click="searchAllCommands()" ng-disabled="selected_server.length==0 || search_all.length==0"  type="button">Buscar</button>
                              </span>
                        </div><!-- /input-group -->
                        <br>

                    </div>

                    <div ng-if="active_command!='ALL'">
                        <button class="btn btn-success btn-lg btn-block" ng-click="showLog()" ng-disabled="selected_server.length==0 || active_command==null" >Mostrar log</button>
                    </div>

                </div>
                <div class="tab-block" ng-show="tab=='player'">

                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-group" >
                                <li  class="list-group-item" ng-click="group_by='nick';results_hash=[]"  ng-checked="group_by=='nick'" ng-class="{'active':group_by=='nick'}">
                                    <label>
                                        Organizar por nick
                                    </label>
                                </li>
                                <li  class="list-group-item" ng-click="group_by='hash';results_hash=[];"  ng-checked="group_by=='hash'" ng-class="{'active':group_by=='hash'}">
                                    <label>
                                        Organizar por hash
                                    </label>
                                </li>
                                <li  class="list-group-item" ng-click="group_by='data';results_hash=[]"  ng-checked="group_by=='data'" ng-class="{'active':group_by=='data'}">
                                    <label>
                                        Organizar por fecha/hora
                                    </label>
                                </li>
                                <li  class="list-group-item" ng-click="group_by='ip';results_hash=[]"  ng-checked="group_by=='ip'" ng-class="{'active':group_by=='ip'}">
                                    <label>
                                        Organizar por IP
                                    </label>
                                </li>
                            </ul>

                        </div>
                        <div class="col-md-6">
                            <ul class="list-group"   ng-init="hide_duplica='true'">

                                <li  class="list-group-item" ng-click="hide_duplica='true';results_hash=[]" ng-class="{'active':hide_duplica=='true'}">
                                    <label>
                                        Ocultar duplicados
                                    </label>
                                </li>
                                <li  class="list-group-item" ng-click="hide_duplica='false';results_hash=[]" ng-class="{'active':hide_duplica=='false'}">
                                    <label>
                                        Mostrar duplicados
                                    </label>
                                </li>
                            </ul>

                        </div>
                    </div>

                    <form ng-submit="searchHash()">

                        <div class="input-group input-group-lg mt-3" >
                            <input type="text" class="form-control" id="search"  ng-click="results_hash=[]" ng-model="search" placeholder="Buscar...">
                            <span class="input-group-btn">
                        <button class="btn btn-success btn-lg" ng-click="searchHash()" ng-disabled="selected_server.length==0 || search.length==0"  type="button">Buscar</button>
                      </span>
                        </div><!-- /input-group -->
                    </form>

                </div>

            </div>


    </div>
    </div>


    <div class="container p-4">
        <div class="row"  ng-hide="selected_server.length==0"  ng-show="tab=='default'">
            <div class="col-md-12">
                <div ng-show="loading" class="logs-loading text-center py-5">
                    <div class="logs-spinner" role="status" aria-label="Cargando"></div>
                    <div class="logs-loading-text mt-3">Cargando</div>
                </div>
                <div ng-show="results.server_log">

                    <div class="well well-sm" ng-init="filter_list=''">
                        <input class="form-control" ng-model="filter_list" class="form-control form-lg" placeholder="Filtrar">
                    </div>

                    <div class="logs-paging-bar d-flex flex-wrap align-items-center justify-content-between mb-2">
                        <small class="text-muted">
                            Mostrando
                            <b>{{ (filteredLogs.length < logVisible) ? filteredLogs.length : logVisible }}</b>
                            de
                            <b>{{ filteredLogs.length }}</b>
                            registros
                        </small>
                        <button type="button"
                                class="btn btn-success btn-sm"
                                ng-show="logVisible < filteredLogs.length"
                                ng-click="loadMoreLogs()">
                            Cargar mas ({{ logPageSize }})
                        </button>
                    </div>

                    <table class="table table-hover table-sm small">
                        <thead>
                        <tr>
                            <th style="width: 100px">
                                Servidor
                            </th>
                            <th >
                                Fecha
                            </th>
                            <th >
                                Comando
                            </th>
                            <th>
                                Autores
                            </th>
                            <th>
                                Contenido
                            </th>
                        </tr>
                        </thead>
                        <tr ng-repeat="item in filteredLogs = (results.server_log | filter:filter_list) | limitTo:logVisible">
                            <td >
                                {{ item.server }}
                            </td>
                            <td>
                                {{ item.date  }} <b>{{ item.hour }}</b>
                            </td>
                            <td >
                                <span class="text-{{ item.color }}">{{ item.command }}</span>
                            </td>
                            <td>
                                <b>'{{ item.players }}'</b>
                            </td>
                            <td>
                                {{ item.content }}
                            </td>
                        </tr>
                    </table>

                    <div class="logs-paging-bar text-center mt-3 mb-2" ng-show="logVisible < filteredLogs.length">
                        <button type="button" class="btn btn-success" ng-click="loadMoreLogs()">
                            Cargar mas ({{ logPageSize }}) â€”
                            quedan {{ filteredLogs.length - logVisible }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div ng-show="loading_hash" class="logs-loading text-center py-5">
            <div class="logs-spinner" role="status" aria-label="Buscando"></div>
            <div class="logs-loading-text mt-3">Buscando...</div>
        </div>
        <div   ng-show="results_hash.length!=0">
            <div  ng-show="tab=='player'" >

                <table class="table table-hover table-sm small">
                    <thead>
                    <tr>
                        <th>
                            Servidor
                        </th>
                        <th>
                            Fecha
                        </th>
                        <th>
                            Hash
                        </th>
                        <th>
                            Estado
                        </th>
                        <th>
                            Nivel Steam
                        </th>
                        <th>
                            Estado del jugador
                        </th>
                        <th style="min-width:200px;">
                            Nick
                        </th>
                        <th style="min-width: 160px; white-space: nowrap;">
                            Direccion IP
                        </th>
                    </tr>
                    </thead>
                    <tbody  ng-repeat="(keyGroup,lines) in results_hash">

                    <tr>
                        <td colspan="8" style="background: #eeeeee">
                            <b ng-show="group_by=='nick'">Nick:</b>
                            <b ng-show="group_by=='hash'">Hash:</b>
                            <b ng-show="group_by=='data'">Fecha:</b>
                            <b ng-show="group_by=='ip'">IP:</b>
                            {{ keyGroup  }}
                        </td>
                    </tr>
                    <tr ng-repeat="line in lines">
                        <td>
                            {{ line.server }}
                        </td>
                        <td>
                            {{ line.data }}
                        </td>
                        <td>
                            <code>{{ line.hash  }}</code>
                        </td>
                        <td>
                            <div ng-if="line.tags.length==0"><span class="badge badge-warning">Cuenta nueva</span></div>
                            <div ng-repeat="tag in  line.tags ">
                        <span class="badge badge-success" ng-if="tag==='LEGACY'">
                            Legacy
                        </span>
                                <div class="badge badge-danger"  ng-if="tag==='VAC BANNED'">
                                    Ban VAC
                                </div>
                            </div>
                        </td>
                        <td>
                        <span class="badge badge-danger" ng-if="line.steam_level==='0'">
                            Riesgo alto
                        </span>
                            <span class="badge badge-info" ng-if="line.steam_level==='1'">
                            Riesgo medio
                        </span>
                            <span class="badge badge-success" ng-if="line.steam_level==='2'">
                            Riesgo bajo
                        </span>
                        </td>
                        <td>
                            <span ng-if="line.whitelisted" class="badge badge-success" title="Whitelist">En whitelist</span>
                            <span ng-if="line.banned" class="badge badge-danger mr-1" title="BANEADO">
                                <span  ng-if="line.banned_detail=='perm'" >
                                    Baneado
                                </span>
                                <span class="ml-1" ng-if="line.banned_detail=='timeban'" >
                                    Ban temporal
                                </span>
                            </span>
                        </td>
                        <td>
                            <a ng-click="getPlayerInfo(line.nick)" data-toggle="modal" data-target="#myModal" class="text-primary">{{ line.nick  }}</a>
                        </td>
                        <td style="white-space: nowrap; vertical-align: middle;">
                            <span style="display: inline-flex; align-items: center; flex-wrap: nowrap; white-space: nowrap; gap: 6px;">
                                <img style="width: 24px; height: 18px; flex-shrink: 0; display: block;"
                                     ng-src="./flag.php?ip={{ line.ip }}"
                                     ng-if="line.ip"
                                     alt=""
                                     title="Pais">
                                <span style="white-space: nowrap;">{{ line.ip }}</span>
                            </span>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>

    <!-- Modal -->
    <div id="myModal" class="modal fade" role="dialog">
        <div class="modal-dialog" style="max-width: 100%!important;">

            <!-- Modal content-->
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title">Historial de: <b> {{ active_nickname }}</b></h4>
                    <button type="button" class="close" data-dismiss="modal">&times;</button>
                </div>
                <div class="modal-body p-0">
                    <div ng-show="!result_player.server_log" class="logs-loading text-center py-5">
                        <div class="logs-spinner" role="status" aria-label="Cargando"></div>
                        <div class="logs-loading-text mt-3">Cargando</div>
                    </div>
                    <div ng-show="result_player.server_log">
                        <div class="logs-paging-bar d-flex flex-wrap align-items-center justify-content-between px-3 py-2">
                            <small class="text-muted">
                                Mostrando
                                <b>{{ (result_player.server_log.length < playerLogVisible) ? result_player.server_log.length : playerLogVisible }}</b>
                                de
                                <b>{{ result_player.server_log.length }}</b>
                                registros
                            </small>
                            <button type="button"
                                    class="btn btn-success btn-sm"
                                    ng-show="playerLogVisible < result_player.server_log.length"
                                    ng-click="loadMorePlayerLogs()">
                                Cargar mas ({{ logPageSize }})
                            </button>
                        </div>
                        <div style="height: <?php echo $config['modal_height']; ?>; overflow-x: scroll">
                            <table class="table table-sm table-condensed table-hover">
                                <thead>
                                <tr>
                                    <th>
                                        Servidor
                                    </th>
                                    <th>
                                        Fecha
                                    </th>
                                    <th>
                                        Comando
                                    </th>
                                    <th>
                                        Autores
                                    </th>
                                    <th>
                                        Contenido
                                    </th>
                                </tr>
                                </thead>
                                <tr ng-repeat="item in result_player.server_log | limitTo:playerLogVisible">
                                    <td class="">
                                        {{ item.server }}
                                    </td>
                                    <td class="">
                                        {{ item.date  }} <b>{{ item.hour }}</b>
                                    </td>
                                    <td class="">
                                        <span class="text-{{ item.color }}">{{ item.command }}</span>
                                    </td>
                                    <td class="">
                                        <b>'{{ item.players }}'</b>
                                    </td>
                                    <td>
                                        {{ item.content }}
                                    </td>
                                </tr>
                            </table>
                        </div>
                        <div class="logs-paging-bar text-center py-3" ng-show="playerLogVisible < result_player.server_log.length">
                            <button type="button" class="btn btn-success" ng-click="loadMorePlayerLogs()">
                                Cargar mas ({{ logPageSize }}) â€”
                                quedan {{ result_player.server_log.length - playerLogVisible }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>


    <div class="logs-footer">
        <div class="text-center">
            <small class="text-muted">Creado por gerbesf   -   Adaptado por Chaziz</small>
        </div>
    </div>


    <?php latam_render_footer(['pr_nav' => true]); ?>
</body>
</html>
