
import {AgentiaCommand} from '@copado/agentia-plugin-sdk'
import {Flags} from '@oclif/core'
import {spawnSync} from 'node:child_process'
import {existsSync} from 'node:fs'
import path from 'node:path'

export default class CpqValidate extends AgentiaCommand {
  static override description =
    'Validate a Salesforce CPQ change request using CPQ Guardian'

  static override examples = [
    '<%= config.bin %> <%= command.id %> --change sample_data/change_request_live_valid.json',
    '<%= config.bin %> <%= command.id %> --change sample_data/change_request_live_invalid.json --salesforce --target-org GuardianDev',
  ]

  static override flags = {
    change: Flags.string({
      char: 'c',
      description: 'Path to the change-request JSON file',
      required: true,
    }),
    salesforce: Flags.boolean({
      description: 'Read the product catalog from Salesforce',
      default: false,
    }),
    'target-org': Flags.string({
      description: 'Salesforce CLI org alias (required with --salesforce)',
    }),
    rules: Flags.string({
      description: 'Optional CPQ Guardian rules overlay JSON path',
    }),
  }

  public async run() {
    const {flags} = await this.parse(CpqValidate)

    if (flags.salesforce && !flags['target-org']) {
      this.error('--target-org is required when using --salesforce')
    }

    // Resolve the repository root from the current working directory.
    const projectRoot = process.cwd()

    const validator = path.join(projectRoot, 'src', 'guardian.py')
    const changeFile = path.resolve(projectRoot, flags.change)
    const catalogPath = path.join(projectRoot, 'sample_data', 'catalog.json')

    if (!existsSync(validator)) {
      this.error(
        `CPQ Guardian validator not found: ${validator}. Run this command from the repository root.`,
      )
    }

    if (!existsSync(changeFile)) {
      this.error(`Change request file not found: ${changeFile}`)
    }

    const args = [validator]

    if (flags.salesforce) {
      args.push('--salesforce', '--target-org', flags['target-org']!)
    } else {
      if (!existsSync(catalogPath)) {
        this.error(`Local catalog not found: ${catalogPath}`)
      }
      args.push('--catalog', catalogPath)
    }

    args.push('--change', changeFile)

    if (flags.rules) {
      const rulesPath = path.resolve(projectRoot, flags.rules)
      if (!existsSync(rulesPath)) {
        this.error(`Rules file not found: ${rulesPath}`)
      }
      args.push('--rules', rulesPath)
    }

    const result = spawnSync('py', args, {
      cwd: projectRoot,
      encoding: 'utf8',
      shell: false,
      windowsHide: true,
    })

    if (result.stdout) this.log(result.stdout.trim())
    if (result.stderr) this.warn(result.stderr.trim())

    if (result.error) {
      this.error(`Could not start Python: ${result.error.message}`)
    }

    if (result.status !== 0) {
      this.error(
        `CPQ Guardian exited with status ${result.status ?? 'unknown'}`,
      )
    }

    return {success: true, output: result.stdout.trim()}
  }
}
