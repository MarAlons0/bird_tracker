from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('index.html') 