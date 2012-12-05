{% extends "partials/layout_app.html.tpl" %}
{% block title %}Apps{% endblock %}
{% block name %}Apps :: {{ app.name }}{% endblock %}
{% block content %}
    <div class="quote">
        To be able to start using you app you need some extra steps to be acomplished.<br />
        The major step is the staring and pushing of the <strong>git repository</strong>.
    </div>
    <div class="separator-horizontal"></div>
    <div class="commands">
        touch README.md<br />
        git init<br />
        git add README.md<br />
        git commit -m "first commit"<br />
        git remote add origin {{ app.git }}<br />
        git push -u origin master<br />
    </div>
{% endblock %}
