const { Resolver } = require('dns').promises;
const r = new Resolver();
r.setServers(['8.8.8.8']);
(async () => {
    try {
        const srv = await r.resolveSrv('_mongodb._tcp.cluster0.8tb8jax.mongodb.net');
        const txt = await r.resolveTxt('cluster0.8tb8jax.mongodb.net');
        require('fs').writeFileSync('dns-result.json', JSON.stringify({ srv, txt }, null, 2));
    } catch (e) {
        console.error(e);
    }
})();
