import '@testing-library/jest-dom'

// jsdom (the test environment) doesn't implement URL.createObjectURL — a real browser API
// used correctly in Investigation.jsx for image previews. Mocked here so file-upload tests
// don't throw; this is a test-environment gap, not a bug in the component itself.
if (typeof URL.createObjectURL === 'undefined') {
  URL.createObjectURL = () => 'blob:mock-url'
}
