import json
from app.controllers.common import json_response
from app.flask_ext import limiter_ip
from flask import Blueprint, request
from app.pkgs.tools.i18b import getI18n
from app.models.async_task import AsyncTask
from app.pkgs.analyzer_code_exception import AnalyzerCodeException, AnalyzerCodeProcessException

bp = Blueprint('plugine', __name__, url_prefix='/plugine')


@bp.route('/repo_analyzer', methods=['GET'])
@json_response
@limiter_ip.limit("1 per 60 second")
def repo_analyzer_plugine():
    _ = getI18n("controllers")

    ip = request.remote_addr or "127.0.0.1"
    type = request.args.get("type")
    repo = request.args.get("repo")
    if type is None or repo is None:
        raise Exception("param error")
    if len(type) == 0 or len(repo) == 0:
        raise Exception("param error")

    count = AsyncTask.get_today_analyzer_code_count(ip, AsyncTask.Search_Process_Key)
    if count > 0:
        process_task = AsyncTask.get_today_analyzer_code_list(ip, AsyncTask.Search_Process_Key)
        if process_task:
            content = json.loads(process_task.task_content)
            repo = content['repo']
            task_no = process_task.token
            raise AnalyzerCodeProcessException("当前有正在处理的任务，请稍后...", 1001, task_no, repo)
        raise AnalyzerCodeException("当前有正在处理的任务，请稍后...", 1001)

    count = AsyncTask.get_today_analyzer_code_count(ip, AsyncTask.Search_Done_key)
    if count >= 3:
        raise AnalyzerCodeException("今日分析次数已经使用完，您可以到平台注册使用", 3001)

    data = {"type": type, "repo": repo}

    task = AsyncTask.create_task(AsyncTask.Type_Analyzer_Code, "分析代码仓库", json.dumps(data), ip)
    if task:
        return {"task_no": task.token}
    else:
        raise AnalyzerCodeException("服务器异常", 5001)


@bp.route('/repo_analyzer_check', methods=['GET'])
@json_response
def repo_analyzer_check():
    task_no = request.args.get("task_no")
    if task_no is None or len(task_no) == 0:
        raise Exception("param error")

    task = AsyncTask.get_task_by_token(task_no)
    if task:
        return {"task_no": task.token, "status": task.task_status, "message": task.task_status_message}
    else:
        raise Exception("查询数据不存在")
