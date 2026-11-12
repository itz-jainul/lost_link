document.addEventListener('DOMContentLoaded', function(){
  const fileInputs = document.querySelectorAll('input[type="file"][name="image"]');
  fileInputs.forEach(function(inp){
    const container = document.getElementById('preview-container') || inp.parentElement;
    const preview = document.createElement('img');
    preview.style.maxWidth = '240px';
    preview.style.borderRadius = '8px';
    preview.style.display = 'none';
    preview.className = 'mt-3';
    container.appendChild(preview);
    inp.addEventListener('change', function(e){
      const f = e.target.files[0];
      if(!f){ preview.style.display='none'; return; }
      const url = URL.createObjectURL(f);
      preview.src = url;
      preview.style.display = 'block';
    });
  });
});
