"""
数据库迁移工具 - 自动检查并添加缺失的字段
"""
import logging
from sqlalchemy import inspect, text
from core.database import engine, Base
from models.task import Task

logger = logging.getLogger(__name__)


def check_and_migrate_database():
    """
    检查数据库并执行迁移
    """
    logger.info("检查数据库结构...")

    try:
        inspector = inspect(engine)

        # 检查 tasks 表是否存在
        if 'tasks' not in inspector.get_table_names():
            logger.info("tasks 表不存在，创建所有表...")
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表创建完成")
            return

        # 检查 tasks 表的字段
        columns = [col['name'] for col in inspector.get_columns('tasks')]
        logger.info(f"tasks 表现有字段: {columns}")

        # 检查并添加缺失字段
        with engine.connect() as conn:
            # 检查 template_config 字段
            if 'template_config' not in columns:
                logger.info("添加 template_config 字段...")
                # SQLite 使用 TEXT 类型存储 JSON
                conn.execute(text("ALTER TABLE tasks ADD COLUMN template_config TEXT"))
                conn.commit()
                logger.info("template_config 字段添加成功")

            # 检查 language 字段
            if 'language' not in columns:
                logger.info("添加 language 字段...")
                conn.execute(text("ALTER TABLE tasks ADD COLUMN language TEXT DEFAULT 'en'"))
                conn.commit()
                logger.info("language 字段添加成功")

            # 可以在这里添加更多字段检查...

        logger.info("数据库迁移检查完成")

    except Exception as e:
        logger.error(f"数据库迁移失败: {e}", exc_info=True)
        # 如果迁移失败，尝试重新创建所有表（这会删除数据）
        try:
            logger.warning("尝试重新创建数据库表...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表重新创建完成")
        except Exception as e2:
            logger.error(f"重新创建表也失败: {e2}", exc_info=True)
            raise


def init_database():
    """
    初始化数据库
    """
    # 先尝试迁移
    check_and_migrate_database()
    # 确保所有表都存在
    Base.metadata.create_all(bind=engine, checkfirst=True)
