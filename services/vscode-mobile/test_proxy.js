const http = require('http');

const MOBILE_STYLE = '@media(max-width:768px){.monaco-workbench{font-size:14px!important}}';
const MOBILE_VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">';

function injectMobileOptimizations(body) {
  if (!body || !body.includes('<head>')) return body;
  
  let modified = false;
  const origLen = body.length;
  
  // 1. Replace viewport
  body = body.replace(/<meta name="viewport"[^>]*\/?>/i, MOBILE_VIEWPORT);
  if (body.includes('maximum-scale=5')) { console.log('Step1 OK'); modified = true; }
  
  // 2. Remove pinch-zoom block
  body = body.replace(/<!-- Disable pinch zooming -->[\s\S]*?<\/script>\s*/i, '');
  if (!body.includes('Disable pinch zooming')) { console.log('Step2 OK'); modified = true; }
  
  // 3. Fix remoteAuthority
  body = body.replace(
    /remoteAuthority(&quot;|")(\s*:\s*)(&quot;|")(localhost|127\.0\.0\.1):8000\3/g,
    'remoteAuthority$1$2$3$4:8001$3'
  );
  if (body.includes('8001')) { console.log('Step3 OK'); modified = true; }
  
  // 4. Inject mobile CSS
  body = body.replace('</head>', '<style>' + MOBILE_STYLE + '</style>\n</head>');
  if (body.includes('max-width:768px')) { console.log('Step4 OK'); modified = true; }
  
  // 5. Mark body
  body = body.replace('<body ', '<body data-zes-mobile="true" ');
  if (body.includes('data-zes-mobile')) { console.log('Step5 OK'); modified = true; }
  
  console.log('Orig length:', origLen, 'New length:', body.length, 'Modified:', modified);
  return body;
}

// Test with actual VS Code response
http.get('http://127.0.0.1:8000/', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk.toString());
  res.on('end', () => {
    console.log('Direct VS Code response length:', data.length);
    console.log('Contains head:', data.includes('<head>'));
    const result = injectMobileOptimizations(data);
    console.log('Result length:', result.length);
    console.log('Has meta scale=5:', result.includes('maximum-scale=5'));
    console.log('Has 8001:', result.includes('8001'));
    console.log('Has data-zes-mobile:', result.includes('data-zes-mobile'));
  });
});
