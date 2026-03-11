const sendBtn = document.getElementById('sendBtn');
const questionInput = document.getElementById('question');
const sqlOutput = document.getElementById('sqlOutput');
const examples = document.getElementById('examples');

sendBtn.addEventListener('click', async () => {
  sqlOutput.textContent = 'Generating...';
  examples.innerHTML = '';

  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: questionInput.value }),
  });

  if (!response.ok) {
    sqlOutput.textContent = `Error: ${await response.text()}`;
    return;
  }

  const data = await response.json();
  sqlOutput.textContent = data.sql;

  for (const ex of data.context_examples) {
    const div = document.createElement('div');
    div.className = 'example';
    div.innerHTML = `<strong>${ex.report_name}</strong> (similarity: ${ex.similarity})
      <p>${ex.description}</p>
      <pre>${ex.sql}</pre>`;
    examples.appendChild(div);
  }
});
