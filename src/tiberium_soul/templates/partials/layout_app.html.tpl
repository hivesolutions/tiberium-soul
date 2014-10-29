{% extends "partials/layout.html.tpl" %}
{% block header %}
    {{ super() }}
    <div class="links sub-links">
        {% if sub_link == "info" %}
            <a href="{{ url_for('show_app', id = app.id) }}" class="active">info</a>
        {% else %}
            <a href="{{ url_for('show_app', id = app.id) }}">info</a>
        {% endif %}
        //
        {% if sub_link == "edit" %}
            <a href="{{ url_for('edit_app', id = app.id) }}" class="active">edit</a>
        {% else %}
            <a href="{{ url_for('edit_app', id = app.id) }}">edit</a>
        {% endif %}
        //
        {% if sub_link == "help" %}
            <a href="{{ url_for('help_app', id = app.id) }}" class="active">help</a>
        {% else %}
            <a href="{{ url_for('help_app', id = app.id) }}">help</a>
        {% endif %}
        //
        {% if sub_link == "restart" %}
            <a href="{{ url_for('restart_app', id = app.id) }}" class="active">restart</a>
        {% else %}
            <a href="{{ url_for('restart_app', id = app.id) }}">restart</a>
        {% endif %}
        //
        {% if sub_link == "delete" %}
            <a href="{{ url_for('delete_app_c', id = app.id) }}" class="active">delete</a>
        {% else %}
            <a href="{{ url_for('delete_app_c', id = app.id) }}">delete</a>
        {% endif %}
    </div>
{% endblock %}
