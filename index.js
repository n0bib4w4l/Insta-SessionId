// index.js - Single file Vercel deployment
export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,POST');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const { username, reporttype, time } = req.query;

    // Validate required parameters
    if (!username || !reporttype || !time) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters',
        usage: 'URL format: /?username=USERNAME&reporttype=TYPE&time=TIMESTAMP',
        example: '/?username=celinevipxo&reporttype=spam&time=1691360000'
      });
    }

    // Instagram API endpoint
    const instagramAPIUrl = 'https://www.instagram.com/api/v1/web/reports/get_frx_prompt/';

    // Headers based on your provided data
    const headers = {
      'Accept': '*/*',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Referer': `https://www.instagram.com/${username}/`,
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
      'X-IG-App-ID': '936619743392459',
      'X-Instagram-AJAX': '1025588585',
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': generateCSRFToken()
    };

    // Form data for the report
    const formData = new URLSearchParams({
      'username': username,
      'report_type': reporttype,
      'timestamp': time,
      'source': 'web'
    });

    console.log(`Report request for ${username} - Type: ${reporttype} - Time: ${time}`);

    // Make request to Instagram API
    const response = await fetch(instagramAPIUrl, {
      method: 'POST',
      headers: headers,
      body: formData.toString()
    });

    const data = await response.json();

    if (response.ok) {
      return res.status(200).json({
        success: true,
        message: `Report submitted for ${username}`,
        data: {
          username,
          reporttype,
          time,
          status: 'submitted',
          response: data
        }
      });
    } else {
      return res.status(response.status).json({
        success: false,
        error: 'Instagram API error',
        status: response.status,
        data: data
      });
    }

  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      message: error.message
    });
  }
}

// Generate a mock CSRF token (you might need to implement proper token generation)
function generateCSRFToken() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}
