{% extends "partials/layout_app.html.tpl" %}
{% block title %}Apps{% endblock %}
{% block name %}Apps :: {{ app.name }}{% endblock %}
{% block content %}
    <div class="form form-simple">
        <dl>
            <dt>
                <label>Name</label>
            </dt>
            <dd>
                <input class="text-field" name="name" value="{{ app.id }}"
                       data-error="{{ errors.id }}" />
                <div class="button" data-submit="true">Rename</div>
            </dd>
            <div class="clear"></div>
        </dl>
        <dl>
            <dt>
                <label>Description</label>
                <p>A Small description for the app, should be easy
                to identify the app from this small text</p>
            </dt>
            <dd>
                <input class="text-field" name="descrption" value="{{ app.description }}"
                       data-error="{{ errors.description }}" />
                <div class="button" data-submit="true">Update</div>
            </dd>
            <div class="clear"></div>
        </dl>
        <dl>
            <dt>
                <label>Environment</label>
                <p>The set of environment variables to be
                passed to the application on start</p>
            </dt>
            <dd>
                {% for key, value in app.env.items() %}
                    <input class="text-field small" name="key" value="{{ key }}" data-disabled="1" />
                    <span class="separator">=</span>
                    <input class="text-field small" name="key" value="{{ value }}" data-disabled="1" />
                {% endfor %}
                <form action="{{ url_for('set_env_app', id = app.id) }}" method="post" class="line">
                    <input class="text-field small" name="key" placeholder="key" data-error="{{ errors.name }}" />
                    <span class="separator">=</span>
                    <input class="text-field small" name="value" placeholder="value" data-error="{{ errors.name }}" />
                    <div class="button" data-submit="true">Add</div>
                </form>
            </dd>
            <div class="clear"></div>
        </dl>
        <dl>
            <dt>
                <label>Domains</label>
                <p>The complete set of domains that point to
                the application</p>
            </dt>
            <dd>
                <div class="link">
                    <a href="http://{{ app.domain }}">{{ app.domain }}</a>
                </div>
                {% for domain in app.domains %}
                    <div class="link">
                        <a href="http://{{ domain }}">{{ domain }}</a>
                    </div>
                {% endfor %}
                <form action="{{ url_for('set_alias_app', id = app.id) }}" method="post" class="line">
                    <input class="text-field" name="alias" placeholder="colony.org" data-error="{{ errors.name }}" />
                    <div class="button" data-submit="true">Add</div>
                </form>
            </dd>
            <div class="clear"></div>
        </dl>
    </div>
{% endblock %}
