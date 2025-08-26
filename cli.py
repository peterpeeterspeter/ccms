#!/usr/bin/env python3
"""
🎯 CCMS Native LangChain CLI - Single Entry Point
==============================================

Command: ccms run --tenant=crashcasino --casino=viage --locale=en-GB

Claude.md Compliance:
✅ Single declarative entry point 
✅ No ad-hoc scripts or per-brand runners
✅ Config-driven via Supabase tables
✅ Native LCEL pipeline execution
"""

import asyncio
import logging
import sys
from typing import Optional

import click
from langchain_core.runnables import RunnableConfig

from ccms_pipeline import ccms_pipeline, CCMSInput, CCMSResult, ComplianceError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """🎯 CCMS - Native LangChain Casino Review Pipeline"""
    pass


@cli.command()
@click.option('--tenant', required=True, help='Tenant slug (e.g., crashcasino)')
@click.option('--casino', required=True, help='Casino slug (e.g., viage)')
@click.option('--locale', default='en-GB', help='Locale code (default: en-GB)')
@click.option('--dry-run', is_flag=True, help='Preview mode - no publishing')
@click.option('--skip-compliance', is_flag=True, help='Skip compliance gates (DANGEROUS)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
def run(
    tenant: str,
    casino: str,
    locale: str,
    dry_run: bool,
    skip_compliance: bool,
    verbose: bool
):
    """
    🚀 Run the complete casino review pipeline
    
    Examples:
        ccms run --tenant=crashcasino --casino=viage --locale=en-GB
        ccms run --tenant=crashcasino --casino=napoleon-games --dry-run
        ccms run --tenant=crashcasino --casino=betsson --skip-compliance
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if skip_compliance:
        logger.warning("⚠️  COMPLIANCE GATES DISABLED - NOT SUITABLE FOR PRODUCTION")
    
    if dry_run:
        logger.info("🧪 DRY RUN MODE - No publishing will occur")
    
    # Run the pipeline
    asyncio.run(_execute_pipeline(
        tenant=tenant,
        casino=casino,
        locale=locale,
        dry_run=dry_run,
        skip_compliance=skip_compliance
    ))


async def _execute_pipeline(
    tenant: str,
    casino: str,
    locale: str,
    dry_run: bool,
    skip_compliance: bool
) -> None:
    """Execute the CCMS pipeline with proper error handling"""
    
    try:
        logger.info(f"🎯 Starting CCMS pipeline: {tenant}/{casino}/{locale}")
        
        # Create pipeline input
        pipeline_input = CCMSInput(
            tenant_slug=tenant,
            casino_slug=casino,
            locale=locale,
            dry_run=dry_run,
            skip_compliance=skip_compliance
        )
        
        # Configure runnable
        config = RunnableConfig(
            configurable={
                "tenant_slug": tenant,
                "casino_slug": casino,
                "locale": locale,
                "dry_run": dry_run,
                "skip_compliance": skip_compliance
            },
            tags=["ccms-pipeline", f"tenant:{tenant}", f"casino:{casino}"],
            metadata={
                "tenant": tenant,
                "casino": casino,
                "locale": locale,
                "execution_mode": "dry_run" if dry_run else "production"
            }
        )
        
        # Execute pipeline
        logger.info("⚡ Executing LCEL pipeline...")
        result: CCMSResult = await ccms_pipeline.ainvoke(pipeline_input.model_dump(), config=config)
        
        # Handle results
        if result.success:
            logger.info("✅ Pipeline completed successfully!")
            
            if result.published_url:
                logger.info(f"📄 Published: {result.published_url}")
            
            if result.media_assets:
                logger.info(f"🖼️  Media: {len(result.media_assets)} assets uploaded")
            
            logger.info(f"⏱️  Total duration: {result.total_duration_ms}ms")
            
            # Print summary
            click.echo("\n" + "="*60)
            click.echo(f"🎯 CCMS PIPELINE COMPLETED")
            click.echo("="*60)
            click.echo(f"Tenant:    {result.tenant_slug}")
            click.echo(f"Casino:    {result.casino_slug}")
            click.echo(f"Locale:    {result.locale}")
            click.echo(f"Status:    {'✅ SUCCESS' if result.success else '❌ FAILED'}")
            
            if result.published_url:
                click.echo(f"URL:       {result.published_url}")
            
            click.echo(f"Duration:  {result.total_duration_ms}ms")
            click.echo(f"Events:    {len(result.events)} pipeline events")
            
            if result.compliance_score:
                click.echo(f"Compliance: {result.compliance_score:.1%}")
            
            click.echo("="*60)
            
        else:
            logger.error("❌ Pipeline failed!")
            if result.error:
                logger.error(f"Error: {result.error}")
            sys.exit(1)
            
    except ComplianceError as e:
        logger.error(f"🚨 COMPLIANCE FAILURE: {e}")
        logger.error("❌ Publication blocked due to compliance violations")
        sys.exit(2)
        
    except KeyboardInterrupt:
        logger.warning("⏹️  Pipeline interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


@cli.command()
@click.option('--tenant', help='Filter by tenant')
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
def config(tenant: Optional[str], format: str):
    """📋 Display configuration hierarchy"""
    from src.tools.supabase_config_tool import supabase_config_tool
    
    # TODO: Implement config display
    click.echo("🚧 Config display not yet implemented")


@cli.command()
@click.option('--casino', required=True, help='Casino to validate')
@click.option('--tenant', default='crashcasino', help='Tenant context')
def validate(casino: str, tenant: str):
    """🔍 Validate casino for pipeline readiness"""
    # TODO: Implement validation checks
    click.echo("🚧 Validation not yet implemented")


@cli.command()
def health():
    """🏥 Check system health and dependencies"""
    click.echo("🏥 CCMS Health Check")
    click.echo("="*40)
    
    # Check pipeline imports
    try:
        from ccms_pipeline import ccms_pipeline
        click.echo("✅ Pipeline imports OK")
    except ImportError as e:
        click.echo(f"❌ Pipeline import failed: {e}")
        return
    
    # Check tools
    try:
        from src.tools.supabase_config_tool import supabase_config_tool
        from src.tools.supabase_research_tool import supabase_research_tool
        from src.tools.wordpress_enhanced_publisher import wordpress_enhanced_publisher
        click.echo("✅ Core tools available")
    except ImportError as e:
        click.echo(f"❌ Tool import failed: {e}")
        return
    
    # Check environment
    import os
    required_env = [
        'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE',
        'WORDPRESS_BASE_URL', 'WORDPRESS_APP_PW',
        'OPENAI_API_KEY'
    ]
    
    missing_env = [var for var in required_env if not os.getenv(var)]
    if missing_env:
        click.echo(f"⚠️  Missing environment variables: {', '.join(missing_env)}")
    else:
        click.echo("✅ Environment variables OK")
    
    click.echo("\n🎯 System ready for pipeline execution")


if __name__ == '__main__':
    cli()