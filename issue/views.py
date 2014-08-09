from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from issue.models import *
from issue.forms import *

import shlex


def profile(request):

    user = User.objects.get(username=request.user)

    c = {
            'groups': user.groups.all(),
            'teams': user.teams.all(),
        }

    return render(request, 'issue/profile.html', c)

def global_permission_list(request):

    permissions = GlobalPermission.objects.all()

    c = {
            'permissions': permissions,
    }

    return render(request, 'issue/global_permission_list.html', c)

def global_permission_edit(request, id=None):

    if id:
        permission = get_object_or_404(GlobalPermission, id=id)
        new = False
    else:
        permission = None
        new = True

    form = GlobalPermissionForm(request.POST or None, instance=permission)

    if request.method == 'POST' and form.is_valid():

        permission = form.save()

        if new:
            messages.success(request, 'Permission added successfully.')
        else:
            messages.success(request, 'Permission updated successfully.')

        return redirect('list-global-permission')

    c = {
            'form': form,
        }

    return render(request, 'issue/global_permission_edit.html', c)

def global_permission_toggle(request, id, perm):

    permission = get_object_or_404(GlobalPermission, id=id)

    # to be sure to dont modify other attribut with the following trick
    if not '-' in perm:
        raise Http404
    perm = perm.replace('-', '_')

    if hasattr(permission, perm):
        print(type(getattr(permission, perm)))
        setattr(permission, perm, not getattr(permission, perm))
        permission.save()
    else:
        raise Http404

    return redirect('list-global-permission')

def global_permission_delete(request, id):

    permission = get_object_or_404(GlobalPermission, id=id)

    permission.delete()

    messages.success(request, 'Permission deleted successfully.')

    return redirect('list-global-permission')

def project_permission_list(request, project):

    permissions = ProjectPermission.objects.filter(project=project)

    c = {
            'project': project,
            'permissions': permissions,
    }

    return render(request, 'issue/project_permission_list.html', c)

def project_permission_edit(request, project, id=None):

    if id:
        permission = get_object_or_404(ProjectPermission, project=project, id=id)
    else:
        permission = None

    form = ProjectPermissionForm(request.POST or None, instance=permission)

    if request.method == 'POST' and form.is_valid():

        permission = form.save(commit=False)
        if not hasattr(permission, 'project'):
            permission.project = project
            messages.success(request, 'Permission added successfully.')
        else:
            messages.success(request, 'Permission updated successfully.')
        permission.save()

        return redirect('list-project-permission', project.name)

    c = {
            'project': project,
            'form': form,
        }

    return render(request, 'issue/project_permission_edit.html', c)

def project_permission_toggle(request, project, id, perm):

    permission = get_object_or_404(ProjectPermission, project=project, id=id)

    # to be sure to dont modify other attribut with the following trick
    if not '-' in perm:
        raise Http404
    perm = perm.replace('-', '_')

    if hasattr(permission, perm):
        print(type(getattr(permission, perm)))
        setattr(permission, perm, not getattr(permission, perm))
        permission.save()
    else:
        raise Http404

    return redirect('list-project-permission', project.name)

def project_permission_delete(request, project, id):

    permission = get_object_or_404(ProjectPermission, project=project, id=id)

    permission.delete()

    messages.success(request, 'Permission deleted successfully.')

    return redirect('list-project-permission', project.name)

def project_list(request):

    if not request.projects.exists():

        messages.info(request, 'Start by creating a project.')

        return redirect('add-project')

    return render(request, 'issue/project_list.html')

def project_add(request):

    form = AddProjectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():

        if Project.objects \
                .filter(display_name__iexact=form.cleaned_data['display_name']) \
                .exists():

            form._errors['display_name'] = ['There is already a project with a similar name.']

        else:

            project = form.save()

            messages.success(request, 'Project added successfully.')

            return redirect('list-issue', project.name)

    c = {
            'form': form,
        }

    return render(request, 'issue/project_add.html', c)

def project_edit(request, project):

    form = EditProjectForm(request.POST or None, instance=project)

    if request.method == 'POST' and form.is_valid():

        if Project.objects \
                .filter(display_name__iexact=form.cleaned_data['display_name']) \
                .exclude(pk=project.pk).exists():

            form._errors['display_name'] = ['There is already a project with a similar name.']

        else:

            project = form.save()

            messages.success(request, 'Project modified successfully.')

            return redirect('list-issue', project.name)

    c = {
            'project': project,
            'form': form,
        }

    return render(request, 'issue/project_edit.html', c)

def project_delete(request, project):

    project.delete()

    messages.success(request, 'Project deleted successfully.')

    return redirect('list-project')

def issue_list(request, project):

    issues = project.issues

    is_open = ''
    is_close = ''
    is_all = ''
    is_all_query = ""

    query = request.GET.get('q', '')

    if query == '':
        query = 'is:open'

    syntaxe_error = False
    for constraint in shlex.split(query):

        if constraint == '*':
            continue

        args = constraint.split(':')

        if len(args) != 2:
            messages.error(request, 'There is a syntaxe error in your filter.')
            issues = None
            break

        key = args[0]
        value = args[1]

        if key == '':
            continue

        elif key == 'is':
            if value == 'open':
                issues = issues.filter(closed=False)
                is_open = ' active'
            elif value =='close':
                issues = issues.filter(closed=True)
                is_close = ' active'
            else:
                messages.error(request, "The keyword 'is' must be followed by 'open' or 'close'.")
                issues = None
                break

        elif key == 'label':
            try:
                label = Label.objects.get(project=project,name=value,deleted=False)
            except ObjectDoesNotExist:
                messages.error(request, "The label '%s' does not exist or has been deleted." %value)
                issues = None
                break
            else:
                issues = issues.filter(labels=label)

        elif key == 'milestone':
            try:
                milestone = Milestone.objects.get(project=project,name=value)
            except ObjectDoesNotExist:
                messages.error(request, "The milestone '%s' does not exist." %value)
                issues = None
                break
            else:
                issues = issues.filter(milestone=milestone)

        elif key == 'author' or key == 'user':
            if User.objects.filter(username=value).exists():
                issues = issues.filter(author__username=value)
            else:
                messages.error(request, "The user '%s' does not exist." %value)
                issues = None
                break

        else:
            messages.error(request, "Unknow '%s' filtering criterion." %key)
            issues = None
            break

        if key != 'is':
            is_all_query += ' ' + constraint

    if issues:
        issues = issues.extra(order_by=['-opened_at'])

    if is_open == '' and is_close == '':
        is_all = ' active'

    c = {
            'project': project,
            'issues': issues,
            'query': query,
            'is_open': is_open,
            'is_close': is_close,
            'is_all': is_all,
            'is_all_query': is_all_query[1:],
        }

    return render(request, 'issue/issue_list.html', c)

def issue_edit(request, project, issue=None):

    if issue:
        issue = get_object_or_404(Issue, project=project.name, id=issue)
        init_data = {'title': issue.title,
                     'description': issue.description}
    else:
        issue = None
        init_data = None

    form = IssueForm(request.POST or init_data)

    if request.method == 'POST' and form.is_valid():

        title = form.cleaned_data['title']
        description = form.cleaned_data['description']

        if issue:

            modified = False

            if issue.title != title:
                old_title = issue.title
                issue.title = title
                issue.save()
                author = User.objects.get(username=request.user.username)
                event = Event(issue=issue, author=author, code=Event.RENAME,
                        args={'old_title': old_title, 'new_title': title})
                event.save()
                modified = True

            if issue.description != description:
                issue.description = description
                modified = True

            if modified:
                messages.success(request, 'Issue updated successfully.')
            else:
                messages.info(request, 'Issue not modified.')

        else:

            author = User.objects.get(username=request.user.username)
            issue = Issue(title=title, author=author,
                    project=project, id=Issue.next_id(project))
            issue.save()
            issue.description = description
            messages.success(request, 'Issue created successfully.')

        return redirect('show-issue', project.name, issue.id)

    c = {
            'project': project,
            'form': form,
            'issue': issue,
        }

    return render(request, 'issue/issue_edit.html', c)

def issue(request, project, issue):

    issue = get_object_or_404(Issue, project=project, id=issue)

    labels = Label.objects.filter(project=project, deleted=False) \
            .exclude(id__in=issue.labels.all().values_list('id'))
    milestones = Milestone.objects.filter(project=project)
    if issue.milestone:
        milestones = milestones.exclude(name=issue.milestone.name)

    events = issue.events.all()

    c = {
            'labels': labels,
            'milestones': milestones,
            'project': project,
            'issue': issue,
            'events': events,
        }

    return render(request, 'issue/issue.html', c)

def issue_comment(request, project, issue, comment=None):

    issue = get_object_or_404(Issue, project=project, id=issue)

    if comment:
        event = get_object_or_404(Event, code=Event.COMMENT, issue=issue, id=comment)
        init_data = { 'comment': event.additionnal_section }
    else:
        event = None
        init_data = None

    form = CommentForm(request.POST or init_data)

    if request.method == 'POST' and form.is_valid():

        comment = form.cleaned_data['comment']

        if event:

            if event.additionnal_section != comment:
                event.additionnal_section = comment
                event.save()
                messages.success(request, 'Comment modified successfully.')
            else:
                messages.info(request, 'Comment not modified.')

        else:

            author = User.objects.get(username=request.user.username)
            event = Event(issue=issue, author=author, 
                    code=Event.COMMENT, additionnal_section=comment)
            event.save()
            messages.success(request, 'Comment added successfully.')

        return redirect('show-issue', project.name, issue.id)

    c = {
            'project': project,
            'issue': issue,
            'form': form,
        }

    return render(request, 'issue/issue_comment.html', c)

def issue_close(request, project, issue):

    issue = get_object_or_404(Issue, project=project, id=issue, closed=False)

    issue.closed = True
    issue.save()

    author = User.objects.get(username=request.user.username)
    event = Event(issue=issue, author=author, code=Event.CLOSE)
    event.save()

    return redirect('list-issue', project.name)

def issue_reopen(request, project, issue):

    issue = get_object_or_404(Issue, project=project, id=issue, closed=True)

    issue.closed = False
    issue.save()

    author = User.objects.get(username=request.user.username)
    event = Event(issue=issue, author=author, code=Event.REOPEN)
    event.save()

    return redirect('show-issue', project.name, issue.id)

def issue_delete(request, project, issue):

    issue = get_object_or_404(Issue, project=project, id=issue)

    issue.delete()

    messages.success(request, 'Issue deleted successfully.')

    return redirect('list-issue', project.name)

def issue_add_label(request, project, issue, label):

    issue = get_object_or_404(Issue, project=project, id=issue)
    label = get_object_or_404(Label, project=project, id=label)
    author = User.objects.get(username=request.user.username)

    issue.add_label(author, label)

    return redirect('show-issue', project.name, issue.id)

def issue_remove_label(request, project, issue, label):

    issue = get_object_or_404(Issue, project=project, id=issue)
    label = get_object_or_404(Label, project=project, id=label)
    author = User.objects.get(username=request.user.username)

    issue.remove_label(author, label)

    return redirect('show-issue', project.name, issue.id)

def issue_add_milestone(request, project, issue, milestone):

    issue = get_object_or_404(Issue, project=project, id=issue)
    milestone = get_object_or_404(Milestone, project=project, name=milestone)
    author = User.objects.get(username=request.user.username)

    issue.add_milestone(author, milestone)

    return redirect('show-issue', project.name, issue.id)

def issue_remove_milestone(request, project, issue, milestone):

    issue = get_object_or_404(Issue, project=project, id=issue)
    milestone = get_object_or_404(Milestone, project=project, name=milestone)
    author = User.objects.get(username=request.user.username)

    issue.remove_milestone(author, milestone)

    return redirect('show-issue', project.name, issue.id)

def label_list(request, project):

    labels = project.labels.filter(deleted=False)

    c = {
            'project': project,
            'labels': labels,
        }

    return render(request, 'issue/label_list.html', c)

def label_edit(request, project, id=None):

    if id:
        label = get_object_or_404(Label, project=project, id=id)
    else:
        label = None

    form = LabelForm(request.POST or None, instance=label)

    if request.method == 'POST' and form.is_valid():

        similar = Label.objects.filter(project=project,
                name=form.cleaned_data['name'], deleted=False)

        if label:
            similar = similar.exclude(pk=label.pk)

        if similar.exists():

            form._errors['name'] = ['There is already a label with this name.']

        else:

            if label:
                form.save()
                messages.success(request, 'Label modified successfully.')
            else:
                label = form.save(commit=False)
                label.project = project
                label.save()
                messages.success(request, 'Label added successfully.')

            issue = request.GET.get('issue')
            if issue:
                return redirect('add-label-to-issue', project.name, issue, label.id)

            return redirect('list-label', project.name)

    c = {
            'project': project,
            'form': form,
            'label': label,
        }

    return render(request, 'issue/label_edit.html', c)

def label_delete(request, project, id):

    label = get_object_or_404(Label, project=project, id=id)
    author = User.objects.get(username=request.user.username)

    for issue in label.issues.all():
        issue.remove_label(author, label)
    label.deleted = True
    label.save()

    messages.success(request, "Label deleted successfully.")

    return redirect('list-label', project.name)

def milestone_list(request, project):

    show = request.GET.get('show', 'open')

    if show == 'open':
        milestones = project.milestones.filter(closed=False)
    elif show == 'close':
        milestones = project.milestones.filter(closed=True)
    elif show == 'all':
        milestones = project.milestones.all()
    else:
        messages.error(request, 'There is an error in your filter.')
        milestones = None

    c = {
            'project': project,
            'milestones': milestones,
            'show': show,
        }

    return render(request, 'issue/milestone_list.html', c)

def milestone_edit(request, project, name=None):

    if name:
        milestone = get_object_or_404(Milestone, project=project, name=name)
    else:
        milestone = None

    form = MilestoneForm(request.POST or None, instance=milestone)

    if request.method == 'POST' and form.is_valid():

        similar = Milestone.objects.filter(project=project,
                name=form.cleaned_data['name'])

        if milestone:
            similar = similar.exclude(pk=milestone.pk)

        if similar.exists():

            form._errors['name'] = ['There is already a milestone with this name.']

        else:

            if milestone:
                if name != form.cleaned_data['name']:
                    author = User.objects.get(username=request.user.username)
                    for issue in milestone.issues.all():
                        event = Event(issue=issue, author=author, code=Event.CHANGE_MILESTONE,
                                args={'old_milestone': name, 'new_milestone': form.cleaned_data['name']})
                        event.save()
                form.save()
                messages.success(request, 'Milestone modified successfully.')
            else:
                milestone = form.save(commit=False)
                milestone.project = project
                milestone.save()
                messages.success(request, 'Milestone added successfully.')

            issue = request.GET.get('issue')
            if issue:
                return redirect('add-milestone-to-issue', project.name, issue, milestone.name)

            return redirect('list-milestone', project.name)

    c = {
            'project': project,
            'form': form,
            'milestone': milestone,
        }

    return render(request, 'issue/milestone_edit.html', c)

def milestone_close(request, project, name):

    milestone = get_object_or_404(Milestone, project=project, name=name)

    milestone.closed = True
    milestone.save()

    return redirect('list-milestone', project.name)

def milestone_reopen(request, project, name):

    milestone = get_object_or_404(Milestone, project=project, name=name)

    milestone.closed = False
    milestone.save()

    return redirect('list-milestone', project.name)

def milestone_delete(request, project, name):

    milestone = get_object_or_404(Milestone, project=project, name=name)
    author = User.objects.get(username=request.user.username)

    for issue in milestone.issues.all():
        issue.remove_milestone(author, milestone)
    milestone.delete()

    messages.success(request, "Label deleted successfully.")

    return redirect('list-milestone', project.name)
