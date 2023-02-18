use rhai::{
    Engine,
    EvalAltResult,
};

use crate::{
    BotAPI,
    Message,
};

pub trait Action {
    fn call(
        &self,
        api: &BotAPI,
        message: &Message,
        rhai_engine: &Engine,
    );
}
