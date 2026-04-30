module.exports = {
  ci: {
    collect: {
      staticDistDir: './dist',
      url: ['http://localhost/index.html'],
      numberOfRuns: 1,
    },
    assert: {
      assertions: {
        'categories:performance':     ['error', { minScore: 0.90 }],
        'categories:accessibility':   ['error', { minScore: 0.95 }],
        'categories:best-practices':  ['error', { minScore: 0.95 }],
        'categories:seo':             ['error', { minScore: 0.95 }],
      },
    },
    upload: { target: 'filesystem', outputDir: './lighthouse-results' },
  },
};
