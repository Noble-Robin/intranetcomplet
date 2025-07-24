# Ajouter un bouton "Dupliquer" dans la liste des cours Django

Cette documentation explique comment ajouter un bouton **Dupliquer** dans la table des cours de votre application Django, afin de permettre la duplication rapide d’un cours existant.

---

## 1. Vue Django pour la duplication

Créez une vue qui duplique un objet `Course` :

```python
# moodle/caplogy_app/views.py

from django.shortcuts import get_object_or_404, redirect
from .models import Course

def duplicate_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.pk = None  # Prépare la copie
    course.title += " (copie)"  # Optionnel : ajoute un suffixe
    course.save()
    return redirect('courses_list')  # Redirige vers la liste des cours
```

---

## 2. URL pour la duplication

Ajoutez une route dans votre fichier d’URLs :

```python
# moodle/caplogy_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ... autres routes ...
    path('courses/<int:pk>/duplicate/', views.duplicate_course, name='duplicate_course'),
]
```

---

## 3. Bouton dans le template HTML

**Où ajouter le bouton ?**

Le bouton doit être ajouté dans le fichier de template qui affiche la liste des cours.  
Dans ta structure, il s'agit de :

```
moodle/caplogy_app/templates/caplogy_app/courses.html
```

Dans ce fichier, repère la boucle qui affiche chaque cours (généralement `{% for course in courses %}`) et ajoute le bouton dans la colonne "Actions" du tableau :

```html
<!-- moodle/caplogy_app/templates/caplogy_app/courses.html -->
<td>
    <a href="{% url 'duplicate_course' course.pk %}" class="btn btn-warning">Dupliquer</a>
    <a href="{% url 'edit_course' course.pk %}" class="btn btn-primary">Modifier</a>
    <a href="{% url 'delete_course' course.pk %}" class="btn btn-danger">Supprimer</a>
</td>
```

---

## 4. Sécurité et permissions

- Ajoutez le décorateur `@login_required` sur la vue si nécessaire.
- Vérifiez les permissions si seuls certains utilisateurs peuvent dupliquer.

---

## 5. Résultat

Un bouton **Dupliquer** apparaît à côté de "Modifier" et "Supprimer" dans la liste des cours.  
En cliquant dessus, une copie du cours est créée et ajoutée à la liste.

---

**Astuce :**  
Adaptez le code à votre modèle si vous avez des champs spécifiques à exclure ou à modifier lors