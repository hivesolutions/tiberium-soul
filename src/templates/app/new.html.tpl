{% extends "partials/layout.html.tpl" %}
{% block title %}Apps{% endblock %}
{% block name %}New App{% endblock %}
{% block content %}
    <form action="{{ url_for('create_app') }}" method="post" class="form">
        <div class="label">
            <label>App Name</label>
        </div>
        <div class="input">
            <input class="text-field focus" name="name" placeholder="eg: colony" autocomplete="off" value="{{ app.name }}"
                   data-error="{{ errors.name }}" />
        </div>
        <div class="label">
            <label>Description</label>
        </div>
        <div class="input">
            <textarea class="text-field" name="description" placeholder="eg: some words about the app"
                      data-error="{{ errors.description }}">{{ app.description }}</textarea>
        </div>
        <div class="quote">
            By clicking Submit Application, you agree to our Service Agreement and that you have
            read and understand our Privacy Policy.
        </div>
        <span class="button" data-submit="true">Submit Application</span>
    </form>
{% endblock %}
