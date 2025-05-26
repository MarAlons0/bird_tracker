from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app, db
from app.models import User

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.is_active = request.form.get('is_active') == 'true'
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', title='Profile')

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', title='User Management', users=users)

@app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {user.username} has been {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin_users')) 