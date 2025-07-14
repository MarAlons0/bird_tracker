from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import NewsletterSettingsForm
from app.newsletter.models import NewsletterSubscription

@bp.route('/settings/newsletter', methods=['GET', 'POST'])
@login_required
def newsletter_settings():
    form = NewsletterSettingsForm()
    
    # Set initial value for the form
    if current_user.newsletter_subscription:
        form.is_subscribed.data = current_user.newsletter_subscription.is_active
    
    if form.validate_on_submit():
        try:
            # Get or create subscription
            subscription = current_user.newsletter_subscription
            if not subscription:
                subscription = NewsletterSubscription(user_id=current_user.id)
                db.session.add(subscription)
            
            # Update subscription status
            subscription.is_active = form.is_subscribed.data
            db.session.commit()
            
            flash('Newsletter settings updated successfully!', 'success')
            return redirect(url_for('main.newsletter_settings'))
            
        except Exception as e:
            current_app.logger.error(f"Error updating newsletter settings: {str(e)}")
            flash('An error occurred while updating your settings. Please try again.', 'error')
    
    return render_template('settings/newsletter.html', form=form) 