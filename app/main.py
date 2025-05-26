@app.route('/map')
@login_required
def map():
    return render_template('map.html') 