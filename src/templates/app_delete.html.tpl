{% extends "partials/layout_simple.html.tpl" %}
{% block title %}Apps{% endblock %}
{% block name %}Apps :: {{ app.name }}{% endblock %}
{% block content %}
    <div class="box">
        <div class="quote">
            Are you sure you want to delete <strong>{{ app.name }}</strong> ?
        </div>
        <span class="button" data-link="{{ url_for('show_app', id = app.id) }}">Cancel</span>
        //
        <span class="button" data-link="{{ url_for('delete_app', id = app.id) }}" data-submit="true">Confirm</span>
    </div>
{% endblock %}
