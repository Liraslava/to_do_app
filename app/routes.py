from flask import Blueprint, render_template, request, redirect, url_for
from .models import Task
from . import db
from datetime import datetime
from sqlalchemy import case, asc, desc

main = Blueprint('main', __name__)

@main.route('/')
def index():
    sort_type = request.args.get('sort', 'default')

    if sort_type == 'time_asc':
        # Сначала незавершенные с ближайшим сроком, потом завершенные
        tasks = Task.query.order_by(
            Task.is_completed.asc(),
            Task.due_time.asc()
        ).all()
    elif sort_type == 'time_desc':
        tasks = Task.query.order_by(
            Task.is_completed.asc(),
            Task.due_time.desc()
        ).all()
    elif sort_type == 'priority':
        # Сначала незавершенные и просроченные, потом по дате
        tasks = Task.query.order_by(
            Task.is_completed.asc(),
            case(
                (Task.due_time < datetime.now(), 0),  # Просроченные
                else_=1
            ),
            Task.due_time.asc()
        ).all()
    else:
        # Сортировка по умолчанию (по ID или дате создания)
        tasks = Task.query.order_by(Task.id.desc()).all()

    # Помечаем просроченные задачи
    now = datetime.now()
    for task in tasks:
        task.overdue = bool(task.due_time and task.due_time < now and not task.is_completed)

    return render_template('index.html', tasks=tasks, current_sort=sort_type)

@main.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    due_time_str = request.form.get('due_time')

    due_time = None
    if due_time_str:
        due_time = datetime.strptime(due_time_str, '%Y-%m-%dT%H:%M')

    new_task = Task(title=title)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('main.index'))

@main.route('/complete/<int:task_id>')
def complete(task_id):
    task = Task.query.get(task_id)
    task.is_completed = not task.is_completed
    db.session.commit()
    return redirect(url_for('main.index'))

@main.route('/delete/<int:task_id>')
def delete(task_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('main.index'))