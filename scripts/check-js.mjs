/** Platform-independent syntax check for every shipped JavaScript module. */
import {readdirSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const directory = new URL('../assets/', import.meta.url);
for (const name of readdirSync(directory).filter(name => name.endsWith('.js')).sort()) {
  execFileSync(process.execPath, ['--check', fileURLToPath(new URL(name, directory))], {stdio:'inherit'});
}
