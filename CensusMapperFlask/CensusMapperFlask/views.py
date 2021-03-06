#!../env/bin/python

from CensusMapperFlask import app
from db_models import db, User, Map, DataLayer, ValueBreak, ColorScheme, Category, Measure, Numerator, Denominator, DefaultBreak
import flask
from flask import request
from hashlib import md5
from pgconn import API_KEY, secret_key
from uuid import uuid1


# homepage
@app.route('/')
def home():
    return flask.render_template('home.html', home=True)


# tutorial screens
@app.route('/tutorial')
def tutorial():
    return flask.render_template('tutorial.html')

#profile page
@app.route('/profile')
def profile():
    mapcount = Map.query.filter_by(userid=flask.session['userid']).count()
    mapnamelist = [[str(m.mapname),int(m.mapid)] for m in Map.query.filter_by(userid=flask.session['userid'])]
    return flask.render_template('profile.html', mapcount=mapcount, mapnamelist = mapnamelist)

# map rendering for shared links
@app.route('/map_share')
def map_share():
    #gets the userid and mapid from the url
    try:
        user_id = request.args.get('user')
        map_id = request.args.get('map')
    except:
        return flask.render_template('home.html')

    mapobj = Map.query.filter_by(userid=user_id, mapid=map_id).first()
    if mapobj:
                mapname = mapobj.mapname
                centerlat = mapobj.centerlatitude
                centerlong = mapobj.centerlongitude
                zoom = mapobj.zoomlevel
                layers = [int(d.datalayersid) for d in DataLayer.query.filter_by(mapid=map_id).order_by(DataLayer.displayorder)]
                flask.session['displayorder'] = len(layers)
                flask.session.pop('userid', None)
                flask.session.pop('username', None)
                remove_mapid()
                return flask.render_template('main_map.html', mapname=mapname, centerlat=centerlat, centerlong=centerlong, zoom=zoom, categories=category_list(), layers=layers)

# main mapping page
@app.route('/map')
def map():
    if 'userid' in flask.session:
        try:
            map_id = request.args.get('map')
            flask.session['mapid'] = map_id
        except:
            pass
        if 'mapid' in flask.session:
            mapobj = Map.query.filter_by(userid=flask.session['userid'], mapid=flask.session['mapid']).first()
            if mapobj:
                mapname = mapobj.mapname
                centerlat = mapobj.centerlatitude
                centerlong = mapobj.centerlongitude
                zoom = mapobj.zoomlevel
                layers = [int(d.datalayersid) for d in DataLayer.query.filter_by(mapid=flask.session['mapid']).order_by(DataLayer.displayorder)]
                flask.session['displayorder'] = len(layers)
                return flask.render_template('main_map.html', mapname=mapname, centerlat=centerlat, centerlong=centerlong, zoom=zoom, categories=category_list(), layers=layers)
    else:
        new_user_name = 'temp_' + str(uuid1())
        new_user = User(new_user_name, '', '', 'regular')
        db.session.add(new_user)
        db.session.commit()
        flask.session['userid'] = new_user.userid
    
    mapname = 'Untitled Map'
    centerlat = 40
    centerlong = -98.5
    zoom = 4
    new_map = Map(mapname, flask.session['userid'], centerlat, centerlong, zoom)
    db.session.add(new_map)
    db.session.commit()
    flask.session['mapid'] = new_map.mapid
    flask.session['displayorder'] = 0
    
    return flask.render_template('main_map.html', mapname=mapname, centerlat=centerlat, centerlong=centerlong, zoom=zoom, categories=category_list(), layers=[])


# create user request
@app.route('/create_user', methods = ['POST'])
def create_account():
    #new user name input
    new_user_name = str(request.form['new_name'])
    new_email = str(request.form['new_email'])
    new_password1 = md5(str(request.form['new_password1'])).hexdigest()
    new_password2 = md5(str(request.form['new_password2'])).hexdigest()
    new_access = 'regular'
    new_user = User(new_user_name, new_email, new_password1, new_access)
    
    if new_password1 == new_password2:
        #commits the new user to the db
        db.session.add(new_user)
        db.session.commit()
        flask.session['userid'] = new_user.userid
        flask.session['username'] = new_user.username
        remove_mapid()
    
    #flask.flash('New account was successfully created. Please login.')
    return flask.redirect(flask.url_for('home'))

# login user request
@app.route('/login', methods = ['POST'])
def login_to_account():
    #to access a user that logged in
    login_user_name = str(request.form['login_name'])
    login_user_password = md5(str(request.form['login_password'])).hexdigest()
    login_user = User.query.filter_by(username=login_user_name, password=login_user_password).first()
    
    #check password
    if login_user:
        # clean up old maps
        remove_sql = "delete from maps where mapname = 'Untitled Map' and userid = %d" % (login_user.userid)
        db.engine.execute(remove_sql)
        db.session.commit()
        
        flask.session['userid'] = login_user.userid
        flask.session['username'] = login_user.username
        remove_mapid()
        flask.flash('You were successfully logged in')
        return flask.redirect(request.form['sourcepage'])
    
    # flask.flash('Your username or password did not mach. Please try again.')
    return flask.redirect(flask.url_for('home'))

# logout user request
@app.route('/logout')
def logout_of_account():
    #to log out of current session
    flask.session.pop('userid', None)
    flask.session.pop('username', None)
    remove_mapid()
    return flask.redirect(flask.url_for('home'))

# save maps
@app.route('/save_map', methods = ['POST'])
def save_map():
    #updates the db with new map name
    map_name = str(request.form['maptitle'])
    mapobj = Map.query.filter_by(userid=flask.session['userid'], mapid=flask.session['mapid']).first()
    mapobj.mapname = map_name
    db.session.commit()
    
    mapname = mapobj.mapname
    centerlat = mapobj.centerlatitude
    centerlong = mapobj.centerlongitude
    zoom = mapobj.zoomlevel
    layers = [int(d.datalayersid) for d in DataLayer.query.filter_by(mapid=flask.session['mapid']).order_by(DataLayer.displayorder)]
    flask.session['displayorder'] = len(layers)
    return flask.render_template('main_map.html', mapname=mapname, centerlat=centerlat, centerlong=centerlong, zoom=zoom, categories=category_list(), layers=layers)


# get available categories and measures
@app.route('/_get_measures')
def get_measures():
    # extract category id from element id
    categoryid = request.args['categoryid'].split('-')[1]
    measures = []
    measure_list = Measure.query.filter_by(categoryid=categoryid).order_by(Measure.measureid)
    for m in measure_list:
        denom = True if [d.fieldid for d in Denominator.query.filter_by(measureid=m.measureid)] else False
        measures.append([m.measureid, m.description, denom])
    return flask.jsonify(measures=measures)


@app.route('/_get_colors')
def get_colors():
    # extract category id from element id
    layerid = flask.session['censusviz']
    numcats = DataLayer.query.filter_by(datalayersid=layerid).first().numcategories
    colors = ColorScheme.query.filter_by(numcategories=numcats).order_by(ColorScheme.colorschemename, ColorScheme.categorynumber)
    colorlist = []
    for c in colors:
        if c.categorynumber == 1:
            colordict = {'schemename': c.colorschemename, 'values': []}
        colordict['values'].append('rgb(%d,%d,%d)' % (c.redvalue, c.greenvalue, c.bluevalue))
        if c.categorynumber == numcats:
            colorlist.append(colordict)
            colordict = {}
    return flask.jsonify(colorlist=colorlist)


# update map's zoom level and lat/long
@app.route('/_update_layer_info')
def update_layer_info():
    # extract data from passed object
    zoom = request.args['zoomlevel']
    latlong = request.args['latlong']
    print latlong
    update_sql = "update maps set zoomlevel = %d, centerlatitude = %g, centerlongitude = %g where mapid = %d" % (zoom, latlong[0], latlong[1], session['mapid'])
    db.engine.execute(update_sql)
    db.session.commit()
    return flask.jsonify(True)

# add layer for specific measure
@app.route('/_add_measure_layer')
def add_measure_layer():
    # get measure id
    measureid = request.args['measureid'].split('-')[1]
    measure = Measure.query.filter_by(measureid=measureid).first()
    
    # get category
    category = Category.query.filter_by(categoryid=measure.categoryid).first()
    
    # add datalayer to map
    year = 2011
    flask.session['displayorder'] += 1
    displaygeography = 'default'
    displaytype = 'solid choropleth'
    visible = True
    colorschemename = category.defaultcolorscheme
    numcategories = 5
    transparency = 0.8
    
    new_layer = DataLayer(flask.session['mapid'], measureid, year, flask.session['displayorder'], displaygeography, displaytype, visible, colorschemename, numcategories, transparency)
    db.session.add(new_layer)
    db.session.commit()
    new_layer_id = new_layer.datalayersid
    
    # add value breaks
    breaks = [b.maxvalue for b in DefaultBreak.query.filter_by(measureid=measureid, numcategories=numcategories).order_by(DefaultBreak.categorynumber)]
    for b in range(len(breaks)):
        new_value_break = ValueBreak(new_layer_id, b+1, 0 if b == 0 else breaks[b-1], breaks[b])
        db.session.add(new_value_break)
        db.session.commit()
    
    return flask.jsonify(layerid=new_layer_id)


@app.route('/_render_layer')
def render_layer():
    # get layer id
    layerid = int(request.args['layerid'])
    return generate_layer(layerid)


@app.route('/_set_census_viz')
def set_census_viz():
    # get layer id
    layerid = int(request.args['layerid'])
    flask.session['censusviz'] = layerid
    measureid = DataLayer.query.filter_by(datalayersid=layerid).first().measureid
    description = Measure.query.filter_by(measureid=measureid).first().description
    flask.session['censusviztitle'] = description
    return flask.jsonify(layerid=layerid, description=description)


@app.route('/_get_census_viz')
def get_census_viz():
    layerid = int(flask.session['censusviz'])
    print 'Layer is %d' % layerid
    return flask.jsonify(layerid=layerid)


@app.route('/_update_layer')
def update_layer():
    # change in categories?
    layerid = flask.session['censusviz']

    if 'numcats' in request.args:
        numcats = int(request.args['numcats'])
        update_sql = "update datalayers set numcategories = %d where datalayersid = %d" % (numcats, layerid)
        db.engine.execute(update_sql)
        db.session.commit()
        # update value breaks
        remove_sql = "delete from valuebreaks where datalayersid = %d" % layerid
        db.engine.execute(remove_sql)
        db.session.commit()
        measureid = DataLayer.query.filter_by(datalayersid=layerid).first().measureid
        breaks = [b.maxvalue for b in DefaultBreak.query.filter_by(measureid=measureid, numcategories=numcats).order_by(DefaultBreak.categorynumber)]
        for b in range(len(breaks)):
            new_value_break = ValueBreak(layerid, b+1, 0 if b == 0 else breaks[b-1], breaks[b])
            db.session.add(new_value_break)
            db.session.commit()

    # change in colors?
    if 'colorpick' in request.args:
        colorpick = request.args['colorpick']
        update_sql = "update datalayers set colorschemename = '%s' where datalayersid = %d" % (colorpick, layerid)
        db.engine.execute(update_sql)
        db.session.commit()
    
    return flask.jsonify(layerid=layerid)


# get available categories and measures
@app.route('/_get_measureid')
def get_measureid():
    layerid = request.args['layerid']
    measureid = DataLayer.query.filter_by(datalayersid=layerid).first().measureid
    return flask.jsonify(measureid=measureid)


# get available categories and measures
@app.route('/_get_layerid')
def get_layerid():
    # get measure id
    measureid = request.args['measureid'].split('-')[1]
    
    # get map id
    mapid = flask.session['mapid']
    
    # get datalayersid
    layerid = DataLayer.query.filter_by(mapid=mapid, measureid=measureid).first().datalayersid
    
    return flask.jsonify(layerid=layerid)


@app.route('/_remove_layer')
def remove_layer():
    layerid = int(request.args['layerid'])
    print 'Layer to remove is %d' % layerid
    
    # remove from datalayers
    remove_sql = "delete from datalayers where datalayersid = %d" % (layerid)
    db.engine.execute(remove_sql)
    db.session.commit()
    
    # reorder the layers (to do)
    
    # if necessary, get next datalayerid for display
    if flask.session['censusviz'] == layerid:
        nextlayer = DataLayer.query.filter_by(mapid=flask.session['mapid']).order_by(DataLayer.displayorder).first()
        if nextlayer:
            return flask.jsonify(layerid=layerid, nextid=nextlayer.datalayersid)
        else:
            return flask.jsonify(layerid=layerid, remove_all=True)
    
    return flask.jsonify(layerid=layerid)


app.secret_key = secret_key

# some helper functions...

def remove_mapid():
    if 'mapid' in flask.session:
        flask.session.pop('mapid', None)

def category_list():
    return [u.__dict__ for u in Category.query.all()]

def generate_layer(layerid):
    layerinfo = DataLayer.query.filter_by(datalayersid=layerid).first()
    measureid = layerinfo.measureid
    
    # get measure description text
    measure = Measure.query.filter_by(measureid=measureid).first()
    titletext = measure.description
    
    # get colors and breaks
    color_sql = "select c.categorynumber, v.maxvalue, c.redvalue, c.greenvalue, c.bluevalue " + \
                "from datalayers d join colorschemes c on d.colorschemename = c.colorschemename and d.numcategories = c.numcategories " + \
                "  join valuebreaks v ON d.datalayersid = v.datalayersid and v.categorynumber = c.categorynumber " + \
                "where d.datalayersid = %d" % layerid
    colorlist = list(db.engine.execute(color_sql))
    colors = {k: (m,(r,g,b)) for k, m, r, g, b in colorlist}
    
    # write cartocss
    cartocss = "#censusgeo { line-width: .1; line-color: #444444; polygon-opacity: 0; line-opacity: 0; "
    for c in sorted(colors.keys(), reverse=True):
        cartocss += '[measure <= %g] {polygon-fill: rgb(%d,%d,%d)} ' % (colors[c][0],colors[c][1][0],colors[c][1][1],colors[c][1][2])
    
    if layerinfo.displaygeography == 'default':
        cartocss += "[zoom <= 4][geotype = 'state'] { polygon-opacity: %g; line-opacity: 1; } " % (layerinfo.transparency) + \
                    "[zoom > 4][zoom <= 8][geotype = 'county'] { polygon-opacity: %g; line-opacity: 1; } " % (layerinfo.transparency * 0.9) + \
                    "[zoom > 4][zoom <= 8][geotype = 'state'] { polygon-opacity: 0; line-opacity: 1; line-width: 1; line-color: #444444; } " + \
                    "[zoom > 8][geotype = 'tract'] { polygon-opacity: %g; line-opacity: 1; }" % (layerinfo.transparency * 0.8)
    else:
        cartocss += "[geotype = '%s'] { polygon-opacity: %g; line-opacity: 1; }" % (layerinfo.displaygeography, layerinfo.transparency)
    
    cartocss += "}"
    
    #get numerator(s) and denominator(s)
    num = [n.fieldid for n in Numerator.query.filter_by(measureid=measureid)]
    nums = "'" + ("','").join(num) + "'"
    denom = [d.fieldid for d in Denominator.query.filter_by(measureid=measureid)]
    dens = "'" + ("','").join(denom) + "'"
    
    # write sql query
    sqlquery = "SELECT a.cartodb_id,a.geotype,a.the_geom_webmercator, " + \
               "sum(case when b.fieldid in (%s) then cast(b.value as float) else 0 end)" % nums
    if denom:
        sqlquery += " / (sum(case when b.fieldid in (%s) then cast(b.value as float) else 0 end) + 1)" % dens
    
    sqlquery += " measure FROM censusgeo a JOIN censusdata b ON a.fipscode = b.fipscode " + \
                "GROUP BY a.cartodb_id, a.geotype, a.the_geom_webmercator"
    
    # generate bin labels
    bins = [b.maxvalue for b in ValueBreak.query.filter_by(datalayersid=layerid).order_by(ValueBreak.categorynumber)]
    avg_bin = sum(bins[:-1]) / len(bins[:-1])
    bin_labels = []
    
    for c in range(layerinfo.numcategories):
        if avg_bin < 0.1:
            bin_labels.append('%.1f%% to %.1f%%' % (100.0 * 0 if c == 0 else 100.0 * bins[c-1], 100.0 * bins[c]))
        elif avg_bin < 1:
            bin_labels.append('%.0f%% to %.0f%%' % (100.0 * 0 if c == 0 else 100.0 * bins[c-1], 100.0 * bins[c]))
        else:
            bin_labels.append('{0:,}'.format(0 if c == 0 else int(bins[c-1])) + ' to ' + '{0:,}'.format(int(bins[c])))
    
    return flask.jsonify(sqlquery=sqlquery, cartocss=cartocss, bins=bin_labels, colors=colors, titletext=titletext, layerid=layerid)

