import http from 'k6/http';
import { check, sleep } from 'k6';

// 1. Setup configuration
export const options = {
    stages: [
        { duration: '10s', target: 20 }, // Ramp-up to 20 users over 10 seconds
        { duration: '30s', target: 20 }, // Stay at 20 users for 30 seconds
        { duration: '10s', target: 0 },  // Ramp-down to 0 users
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
        http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const EMAIL = __ENV.EMAIL || 'admin@example.com';
const PASSWORD = __ENV.PASSWORD || 'placeholder';

// 2. Setup runs once before the test starts to get the auth token
export function setup() {
    const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, {
        username: EMAIL,
        password: PASSWORD,
    });

    check(loginRes, {
        'logged in successfully': (r) => r.status === 200,
        'has access_token': (r) => r.json('access_token') !== undefined,
    });

    return { token: loginRes.json('access_token') };
}

// 3. Main test function executed by VUs
export default function (data) {
    const headers = {
        'Authorization': `Bearer ${data.token}`,
        'Content-Type': 'application/json',
    };

    // Scenario 1: Fetch Dashboard Summary
    let res = http.get(`${BASE_URL}/api/v1/dashboard/summary`, { headers });
    check(res, {
        'dashboard summary status is 200': (r) => r.status === 200,
    });
    sleep(1);

    // Scenario 2: Fetch Recent Usage Logs
    res = http.get(`${BASE_URL}/api/v1/usage/?limit=50`, { headers });
    check(res, {
        'usage logs status is 200': (r) => r.status === 200,
    });
    sleep(1);

    // Scenario 3: Fetch Cost Breakdown
    res = http.get(`${BASE_URL}/api/v1/usage/cost-breakdown`, { headers });
    check(res, {
        'cost breakdown status is 200': (r) => r.status === 200,
    });
    sleep(1);
}
