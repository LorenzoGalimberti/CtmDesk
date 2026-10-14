from django.shortcuts import render, get_object_or_404, redirect
from .models import Errore
from .forms import ErroreForm

def errore_list(request):
    errori = Errore.objects.filter(owner=request.user)
    return render(request, 'errore_list.html', {'errori': errori})

def errore_create(request):
    if request.method == 'POST':
        form = ErroreForm(request.POST)
        if form.is_valid():
            errore = form.save(commit=False)
            errore.owner = request.user
            errore.save()
            form.save_m2m()
            return redirect('errore_list')
    else:
        form = ErroreForm()
    return render(request, 'errore_form.html', {'form': form})

def errore_update(request, pk):
    errore = get_object_or_404(Errore, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ErroreForm(request.POST, instance=errore)
        if form.is_valid():
            form.save()
            return redirect('errore_list')
    else:
        form = ErroreForm(instance=errore)
    return render(request, 'errore_form.html', {'form': form})

def errore_delete(request, pk):
    errore = get_object_or_404(Errore, pk=pk, owner=request.user)
    if request.method == 'POST':
        errore.delete()
        return redirect('errore_list')
    return render(request, 'errore_confirm_delete.html', {'errore': errore})


def errore_detail(request, pk):
    errore = get_object_or_404(Errore, pk=pk, owner=request.user)
    return render(request, 'errore_detail.html', {'errore': errore})
